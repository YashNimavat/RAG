# Phase 3 research: Measurement first → v0.1

**What this is:** the research and gap audit for Phase 3 (M1 evaluation set, M2 retrieval metrics harness, M3 generation metrics and LLM-as-judge, M4 experimental discipline, M5 failure analysis), done 2026-10-17 by Claude (Opus 5.5) with six research helpers.
**What this is not:** lessons or code. Nothing in the course was changed, nothing was installed, and no LLM, embedding or tracing API was called.

**How it was checked.**
- **Book:** Ch22 (all 19 pages), App p.3–7/23 and p.12/23, Ch3 p.6/14 and p.10–11/14, and Ch1 p.12/14 were opened and read. Their text was extracted only into the session scratchpad and deleted at the end. No run of 15 or more words from the book is copied here.
- **AE book** (*Evals for AI Engineers*): Ch3, Ch4, Ch5, Ch7, Ch9, Ch10 and Ch11 were read in full, and Ch1 and Ch2 in part. Paraphrase only, with section headings as the only verbatim text.
- **Repo:** every cell cited by 02/04 for M1–M5 was opened at the pinned commit (0-based cells).
- **Interview repo:** `07-evaluation-and-observability/questions.md`, `04-rag-and-retrieval/questions.md`, `12-coding-challenges/12_eval_metrics.py` and four company files were read.
- **External sources:** every one was opened by a helper with WebFetch on 2026-10-17. Anything not confirmed is marked **UNVERIFIED**.
- **Not read:** two reads were declined during the session, the body of `concepts/P6_ir_metrics.md` §D.7 and `concepts/C6_v0_pipeline.md` §D.3–D.5. Statements about those sections rest on their headings and on grep hits only.

**Citation keys used below.** Book pages as `Ch22 p.7/19`. AE as `AE ChN, 'section'`. Repo cells as `notebook.ipynb cell N` (0-based). Interview repo as `AIQ <file> Q<n>` (MIT, "Copyright (c) 2026 Om", pinned e080df2). External sources as **[S<n>]**, numbered in the final Sources list.

---

## Summary (read this first)

**The 5 most important gaps across the phase**
1. **The statistics are used long before they are taught.**
   - Cohen's κ appears in M1's self-agreement check (06 §6.5), but κ belongs to M3.
   - The bootstrap, sign/McNemar test, Wilson interval, power and multiple comparisons are used across M1–M4, but no lesson teaches them. Yash has studied none of P6, C1–C6 or M1–M5 (`concept_tracker.csv`).
   - Each needs a short bridge where it is first used. The small-sample warnings from the research also need to reach the lessons: below a few hundred items, normal-approximation intervals understate the uncertainty [S30], and the bootstrap is weak on small test sets [S27].
2. **The judge certification rule leans on κ, which the method source says not to use for judges.**
   - AE says κ is for comparing humans with humans, and that a judge should be scored on both error directions (AE Ch4, NOTE in 'When to Use Other Metrics'). Judging-the-Judges also shows that agreement numbers hide 10-point score gaps [S9].
   - 06 §8.4 certifies on the lower bounds of failure-class recall and κ, and has **no pass-keep (TPR) bound**.
   - judgy's interval holds p_obs fixed [S13].
   - Fix: certify on lower bounds of both class-wise rates, report κ only, and resample p_obs too. This changes D-10/R-03 wording, so it needs a Codex re-review.
3. **Five book ideas have no owner card.**
   - Sampling-based consistency checking (Ch22 p.8/19; SelfCheckGPT [S14]).
   - The noise-ratio robustness sweep (Ch22 p.11–12/19). The evidence for it is mixed: random documents can *help* [S15].
   - Reference text metrics: BLEU, ROUGE and BERTScore (Ch22 p.10/19).
   - MAP (Ch22 p.6/19).
   - Structured LLM output: schemas, enum labels and parse-failure retry. D-22 recommends M3 as its home, but M3's card does not list it.
   - Each needs a teaching place, or an explicit "link only".
4. **Corpus D can hide retrieval failures, and synthetic items make it worse.**
   - The climate PDF is public general knowledge [S26]. CRAG shows LLM-only answers already reach about a third of questions, and adding RAG can *raise* hallucination [S21].
   - LLM-drafted questions are easier than human ones [S23], and a naive generator yields about 95% single-fact questions [S24].
   - So M1 needs hard category quotas and the origin of every item recorded and reported. M3 needs the closed-book control (already in 06 §7.1) plus the oracle-context control (open decision 1).
5. **Nothing for Phase 3 exists yet.**
   - There are no lessons, question files, labs, apply-it tools or LLMOps notebooks. `evaluation/` and `experiments/` hold only README files.
   - 06 §6–§9 is a dense, correct specification written for a reviewer, not a learner.
   - The acceptance suite `sources/verification/corrections/contracts_check.py` already contains reference versions of CE, Group-Recall, Span-Coverage, the snapshot binding check, the group bootstrap, Wilson, Clopper–Pearson, κ and the κ bootstrap. Every verify notebook should cross-check against it rather than re-derive.

**Tools to add, across the phase** (details in each concept's §10; install nothing yet)
- **Nothing new at runtime.** These are already installed: `scipy` 1.18.1 (exact binomial test, Wilson via `binomtest().proportion_ci`, bootstrap), `scikit-learn` 1.9.1 (`cohen_kappa_score`, `ndcg_score`), `jsonschema` 4.26.0 and `pydantic` 2.13.5 (schemas), `pandas`, `plotly`, `pytest`.
- **Dev group, test only:** `ir-measures` 0.4.3 + `pytrec-eval-terrier` 0.5.10. They give an independent cross-check of Hit@k (`Success@k`), MRR and nDCG in M2's T1 tests, and there is a Python 3.12 Windows wheel.
- **Optional cross-check:** `statsmodels` 0.15.0 (exact McNemar, Holm, the κ variance).
- **From `LLMOPS_FOUNDATION.md` §11, when the LLMOps notebooks are built:**
  - `langsmith` 0.14.4: dataset mirror, `evaluate(upload_results=False)`, and its pytest plugin with `LANGSMITH_TEST_TRACKING=false`.
  - `langchain-core` 1.6.6: a retriever wrapper and an LCEL chain over the cache adapters.
  - `arize-phoenix-otel` 0.17.2 + instrumentors: local traces and annotations.
  - `pre-commit`, `nox`.
  - `judgy` 0.1.0: end batch only; about 60 lines if reimplemented.
- **Labelling helper:** a stdlib page in the existing `study/app/` (0 packages). `ipywidgets` 8.1.9 is the fallback.
- **Not added:**
  - `ragas` 0.4.3: hard-depends on `openai` and `langchain-openai`, defaults to an OpenAI model, sends telemetry unless `RAGAS_DO_NOT_TRACK=true`.
  - `deepeval` 4.2.8: PostHog telemetry, reads the project `.env` on import, writes into `.deepeval/`, defaults to OpenAI.
  - TruLens 2.14.0: 152 packages with its dashboard.
  - Label Studio and Argilla: servers, analytics on by default.
  - Their metric *definitions* are read and compared; their code is not used.

**Decisions Yash must make** (each answerable in a word)
1. Add the **oracle-context and whole-document controls** to v0.1, at about 55 Groq calls each? **both / one / none** (recommended: *both*).
2. **Who labels the judge-certification set?** **me / Codex** (recommended: *me*, with Codex labelling blind as a reported second opinion).
3. Does a **"partial"** answer count as a **failure** when the correctness judge is certified? **yes / no** (recommended: *yes*).
4. How are **ambiguous** questions scored before any version handles ambiguity? **either-reading / exclude** (recommended: *either-reading*).
5. Where should the **labelling helper** live? **kit-page / notebook** (recommended: *kit-page*, a page in the existing `study/app/`, with keyboard shortcuts).

**Size of the build work**

| Concept | Size | Why |
|---|---|---|
| M1 eval set | **L** | Schema, loader and snapshot binding (the reference code exists), plus the big human job: about 48–60 hand-verified items with spans, a category grid, splits, a self-agreement pass and the apply-it validator |
| M2 retrieval harness | **M** | Metrics are fully specified with toy values (06 §7.3); the work is the teaching order, the k-sweep and the determinism and regression tests |
| M3 generation metrics | **L** | Many metrics, the human pilot of 30 or more labels with a labelling helper, the structured-output bridge, and the judge wiring that is built now and run only at the end |
| M4 experimental discipline | **M** | Statistics bridge, comparison runner, flip-rate lab and T1 regression test; most formulas already exist in `contracts_check.py` |
| M5 failure analysis | **M** | Method plus a coding-sheet tool; depends on v0 traces from C6, which do not exist yet (BL-1 unticked) |

---

## Concept M1: Building an evaluation set

### 1. Sources checked

- **Book (verified):**
  - Ch22 p.12–13/19: real queries before synthetic ones; expert review promotes synthetic drafts into a golden set; cover fact lookups, multi-hop, no-answer and adversarial queries; the 200–500 size, which the book gives with no source.
  - Ch22 p.17/19: formal evaluation is overkill for knowledge bases under about fifty documents (cited by 06 v0.1).
  - Ch22 p.1/19: the three user complaints.
- **Repo (verified, 0-based cells):**
  - `data/q_a.json`: 44 items with only `question` and `answer`. All 44 answers best-match pages 1–5 of 33, in page order (#0–11 p.1 … #38–43 p.5), so the "pp.1–5" heuristic in 02/04/06 is **confirmed**.
  - `evaluation/evalute_rag.py` L133–L138: a fresh LLM question list on every run, split on newlines.
  - `all_rag_techniques/choose_chunk_size.ipynb` cells 6 and 12 (details in §4).
- **Course files:**
  - 02 M1 card; 03 M1 row and §6.2–6.3; 04 M1 row.
  - 06 §5.3, §6.1–§6.8 (schema, categories, creation protocol, span labelling, self-agreement, versioning, the 10 seed items D-001…D-010 with verified offsets).
  - 08 D-09, D-17, D-24; Gate C items MX-1 and MX-3.
  - `sources/coach/transfer_seed_bank.md` has **no M1–M5 seeds**, so new scenarios are free to write.
  - `contracts_check.py` functions `validate_binding`, `load_dataset` and `assign_splits`.
- **AE book (paraphrased):**
  - AE Ch3, 'Creating a Starting Dataset of Traces', 'Defining Dimensions', 'Generating Tuples and Queries'.
  - AE Ch7, 'Synthetically Generating Query-Answer Pairs', 'Creating Harder Synthetic Queries', 'Filtering Synthetic Questions', 'Common Pitfalls'.
  - AE Ch4, chapter intro and 'Percent Agreement: Simple but Misleading'.
  - AE Ch5, 'Data Splits for Designing and Validating LLM-as-Judge'.
  - AE Ch9, 'Common Mistakes with CI'.
  - AE Ch10, 'Case Study: EvalGen'.
- **Interview repo:**
  - AIQ `07-evaluation-and-observability/questions.md` Q4, Q12, Q14, Q28, Q29, Q52.
  - AIQ `04-rag-and-retrieval/questions.md` Q45.
  - AIQ `14-company-interview-questions/harvey.md` Q3.
- **External:** [S16] BEIR and TREC qrels · [S17] Chroma chunking report · [S18] SQuAD 2.0 · [S24] Know Your RAG · [S21] CRAG · [S22] RGB · [S23] Rahmani et al. · [S25] CheckList · [S26] Sainz et al. · [S28] McHugh and Artstein & Poesio · [S29] Husain & Shankar FAQ.

### 2. Gap audit

"Studied?" comes from `concept_tracker.csv`: *no* = `not_started`; *exposed* = O1 diagnostic only.

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Why an eval set: you cannot tell whether a change helped without fixed, labelled questions | 02 M1 Failure; Ch22 p.1–2/19 | Partly (Ch22 prose only) | M1 | no | core | Open with the three complaints (Ch22 p.1/19) and `evalute_rag.py` making new questions on every run |
| 2 | Frozen text snapshot, `snapshot_id`, page table, document offsets | 06 §5.3, §6.1, §6.4; D-17 | C1 lesson (written, **not studied**) | C1 | no | bridge | One diagram: PDF → page texts → joined doc text → page table, and why offsets need a frozen extractor |
| 3 | Character offsets and slicing `doc_text[a:b]` | every span | C2 (07 sample lesson; not studied) | C2 | no | bridge | Two lines plus one worked example on D-002 (page 10 [438, 537) → doc [20993, 21092)) |
| 4 | Chunk ids vs spans: why gold must not be chunk ids | 06 §6.4; AE Ch7 stores chunk ids | 06 only | M1 | no | core | Show a chunk id changing under re-chunking. Evidence: BEIR qrels are id-keyed [S16]; Chroma uses excerpt spans [S17] |
| 5 | `evidence_groups`: AND of facts, OR of alternatives; minimal sufficient span | 06 §6.1, §6.4 | 06 only | M1 | no | core | Walk through D-004 (1 group, 2 alternatives) and D-005 (2 groups) |
| 6 | Sufficiency vs uniqueness of a quote (M-03) | 06 §6.4 step 5, §6.7 | 06 only | M1 | no | core | Use the D-007 p.10 extension as the example: a unique quote is not a sufficient span |
| 7 | Hit@k vs Complete-Evidence: why span sufficiency matters | motivates #5 | P6 (written, not studied); P6 only *previews* CE@k (D.7) | P6 → M2 | no | bridge | One sentence and the D-005 fragment counterexample; link to M2 |
| 8 | Question categories and their failing stage | 06 §6.2 | 06 only | M1 | no | core | Category table with one Corpus D example each; cross with page regions (AE Ch3 'Defining Dimensions'; fixes the q_a.json pp.1–5 skew) |
| 9 | Unanswerable kinds: tempting, false-premise, out-of-domain | 06 §6.3 item 4; Gate 3→4 | **missing** (no lesson) | M1 (V3 later) | no | core | Teach the SQuAD 2.0 rule: on-topic, with a plausible same-type distractor [S18]; out-of-domain items are easy, so keep them few |
| 10 | Paraphrase variants, `paraphrase_of`, `group`; variants as invariance tests | 06 §6.1–6.2 | 06 only | M1 | no | core | Link to CheckList INV tests [S25]; report a per-group "all variants right" rate |
| 11 | Human-first writing; LLM drafting from whole pages only; `created_by` | 06 §6.3 items 1–2; D-09 | 06 only | M1 | no | core | Evidence: synthetic sets are easier [S23] and collapse to single facts [S24]. The book also calls for expert review (Ch22 p.12/19) |
| 12 | Leakage: questions from a chunker's chunks; lexical copying; few-shot leaks | 06 §6.3 item 3 | 06 only | M1 | no | core | Lexical-overlap ratio per item; choose_chunk_size's 1.00/1.00 ceiling; AE Ch9 'Common Mistakes with CI' for prompt leakage |
| 13 | Difficulty assigned before any run | 06 §6.3 item 5 | 06 only | M1 | no | core | One line, with the reason (otherwise difficulty is circular) |
| 14 | Dev / test / holdout, assigned by group | 06 §6.3 item 6; MX-3 | 06 only | M1 (M4 uses it) | no | core | Why: selection on dev, one logged test touch, holdout for K1. SQuAD 2.0 split by article too [S18] |
| 15 | Dataset header, `dataset_sha256`, versioning; any edit makes a new hash | 06 §6.6 | 06 only | M1 | no | core | Show that two files differing by one character have different hashes, so comparisons are refused |
| 16 | Self-agreement re-labelling after 7 days; page agreement; span IoU | 06 §6.5 | 06 only | M1 | no | core | Teach IoU on two spans by hand |
| 17 | **Cohen's κ** (in the self-agreement check) | 06 §6.5 | **missing before M1** (M3 owns it) | M3 | exposed (M3, O1 only) | bridge | Short κ box: p_o, p_e, κ; why percent agreement misleads under skew [S28]. Mark "κ not estimable" below 5 items per label (ext review §4 M1) |
| 18 | Sample size and power: 40 is a learning minimum, the book says 200–500 | Gate 3→4; 06 §9.4 | 06 only | M4 | no | next | One paragraph: ~50 items detect only differences of ~18 points (06 §9.4, checked [S31]); link to M4 |
| 19 | Parametric knowledge: a public PDF can be answered closed-book | 06 §7.1; 08 D-02 note | 06 only | M3 | exposed | bridge | One paragraph [S26]; prefer corpus-specific and exact-term items; the closed-book control is M3's |
| 20 | Unlabelled-but-correct evidence ("holes") | M5 review of "retrieval bad / answer good" | **missing** | M1 | no | core | List every sufficient alternative per group; BEIR measured how holes bias labels toward lexical systems [S16] |
| 21 | JSONL and schema validation | the loader | **missing** | M1 | no | core | Validate with a JSON Schema in the lab; `split: "unassigned"` is refused in scored runs |
| 22 | Ambiguous items: how they are scored before any version handles ambiguity | 06 §6.2 | **missing** (no owner; ext review §7 row 7) | M1 / V3 | no | core | Depends on decision 4; until it is made, score on either reading and tag the item |
| 23 | Corpus T eval set (needed for decisions; D is general knowledge) | 06 §10, §11; Gate 2→3 | 06 only | M1 | no | core | Same protocol; T is blocked until DEC-3 is chosen (phase note 3) |

### 3. Quiz coverage

There is no `study/questions/M1_questions.md` yet. Needed questions (titles only; one question per turn, reply template per FORMAT):
- **R:** Why do we store gold evidence as character spans, not chunk ids? · What do the AND and OR in `evidence_groups` mean? · Name the three kinds of unanswerable question and the easy one. · What makes two items belong to the same `group`?
- **A:** Given a page text and a quote, compute the span's page and document offsets. · Turn a two-fact question into `evidence_groups` (one group with two alternatives, or two groups?). · Compute span IoU for an old and a new label of the same fact. · Two label passes give 9 of 10 "answerable" in both and agree on 9: compute percent agreement and κ, and say why κ might be undefined.
- **T:** A colleague builds 200 questions with an LLM from 500-character chunks and gets 0.97 Hit@5 on every chunker. What is wrong, and what do you change? · Write one tempting unanswerable for a new PDF and explain how you checked it.
- **Interview (`set=interview`):** AIQ 04 Q45, "How do you build a golden evaluation set for RAG without months of labelling?". Second choice: AIQ 07 Q29 on synthetic data and its failure modes.

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| M1-E1 | 02 M1 Repo line ("cell 6: 25 auto-generated questions") | Cell 6 **samples** 25 from a larger LLM-generated pool (`DatasetGenerator.from_documents(documents[0:20]).generate_questions_from_nodes()`), with no seed. `documents` loads every file in `data/`, so `[0:20]` is not necessarily the climate PDF | "25 sampled, unseeded, from an LLM question pool over the first 20 loaded documents (any file in `data/`)" |
| M1-E2 | 02 M1 and 06 §6.3 on cell 12 | Confirmed ceiling and staleness. The saved warning quotes `ServiceContext`, while cell 10 now uses `Settings`, and the execution counts are out of order | Add the two staleness signs as evidence |
| M1-E3 | 06 §6.5 | Uses κ before it is taught (M3) and with ~10 items; one moved label can make κ negative (ext review §7 row 8) | Teach a κ bridge in M1, or move κ to the M3 re-label check and keep page agreement and IoU here |
| M1-E4 | `.claude/skills/rag-evaluation` and `synthetic-data-generation` | Recommend (question, answer, source-chunk) triples, i.e. chunk-id gold, which 06 §6.3–6.4 bans | Lessons must say the course deliberately departs from this; the skills stay unedited |
| M1-E5 | 06 §6.2 / 02 Gate 3→4 "6/6 … lower bound ≈ 0.54" | Correct, but it is the **two-sided** exact bound; the one-sided 95% bound is 0.61 [S31 checks] | Say "two-sided" |
| M1-E6 | 02 M1 Ext line | Cites C#46 (BEIR qrels format) as a model, but BEIR qrels are id-keyed, which is exactly the property the course avoids [S16] | Cite it as the contrast case |

### 5. What the research says

- **Synthetic questions are easier and less varied than human ones.**
  - *Study:* Rahmani et al. (SIGIR 2024) built TREC DL 2023 test queries with T5 and GPT-4 and compared them with 51 real queries [S23].
  - *Result:* system rankings agreed well with the real queries (Kendall τ about 0.82–0.86), but **every system scored higher** on synthetic queries, and GPT-4 queries were nearly twice as long. GPT-4 relevance labels agreed weakly with assessors (κ 0.24–0.26).
  - *What it means:* LLM drafts can rank pipelines but inflate absolute scores.
  - *For your project:* tag `created_by` and always report the human-only subset beside the full set (06 §6.3 already asks for this).
- **Naive generation collapses onto one kind of question.**
  - *Study:* Know Your RAG (IBM, COLING 2025) labelled questions as fact, summary, reasoning or unanswerable [S24].
  - *Result:* a single-prompt generator gave about 95% single-fact questions, and Recall@5 differed by 4.8–42 points across labels.
  - *What it means:* an average over a skewed set hides category effects, and can flip which configuration looks best.
  - *For your project:* enforce 06 §6.2's per-category minimums and always report per category.
- **Unanswerables must be tempting.**
  - *Study:* SQuAD 2.0 had crowdworkers write about 54K unanswerable questions that are on-topic and have a plausible answer of the right type in the paragraph [S18].
  - *Result:* automatically made negatives were much easier (best system +15.4 F1). About half of wrong answers matched the planted plausible answer. An always-abstain baseline scores 48.9 F1.
  - *For your project:* write tempting items to that rule; record the distractor span in `distractor_pages` and in a note, so M5 can count "answered the distractor".
- **A category taxonomy you can borrow.**
  - CRAG (Meta, NeurIPS 2024) uses 8 question types. Simple, multi-hop and false-premise are already in 06; condition, set, comparison, aggregation and post-processing are not [S21].
  - CRAG scores hallucination −1, "I don't know" 0 and correct +1.
  - LLM-only answers reached up to 34% accuracy, and straightforward RAG raised hallucination to 25–32%.
  - *For your project:* consider a *comparison* or *aggregation* item where Corpus T supports it. Keep CRAG's scoring idea for V3.
- **Labels keyed to ids break, and pools have holes.**
  - BEIR qrels are (query-id, corpus-id, score) [S16].
  - BEIR showed that unjudged relevant passages bias evaluation toward lexical systems: after the holes were judged, ANCE's nDCG@10 rose from 0.654 to 0.735 and BM25's barely moved.
  - Chroma's chunking report scores token-level precision, recall and IoU against exact excerpts. Its stated limits are the same ones the course designs against: an LLM question style, and no search for other relevant passages [S17].
- **Current practice.**
  - The AE authors' FAQ (2026) and AE Ch3 recommend dimensional sampling: hand-write about 20 tuples, then expand each tuple to a query with a separate call, with humans reviewing [S29]. AE Ch7 writes questions from chunks, which the course rejects for leakage reasons.
  - CRAG and SQuAD 2.0 still rely on human writers for the hard categories.
- **Pitfalls with evidence:**
  - lexical copying makes retrieval look easy [S17, S18, S23];
  - category collapse [S24];
  - easy unanswerables [S18];
  - holes [S16];
  - contamination of public documents [S26];
  - percent agreement under skew [S28].
- **How to evaluate the eval set itself:**
  - items per category and per page region;
  - lexical overlap per category;
  - BM25-only and closed-book ceilings (if either solves nearly everything, the set cannot discriminate);
  - an always-abstain baseline on the unanswerables;
  - span and page self-agreement;
  - a hole audit on M5's "retrieval bad, answer good" items.
- **Interview questions:**
  - How many examples do you need, and where do they come from? (AIQ 07 Q4)
  - Why version an eval dataset, and what goes in the version? (AIQ 07 Q12)
  - How would you use synthetic data, and what are the failure modes? (AIQ 07 Q29)
  - How do you evaluate the eval suite itself? (AIQ 07 Q52)
  - How do you build an eval set with no labels when experts are expensive? (harvey.md Q3)

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).** You cannot know whether a change helped until you have a fixed set of questions whose right answers, and the exact text that proves them, are written down in advance. In this course that text is stored as character spans on a frozen copy of the PDF's text, never as chunk ids, so the labels still work when you change the chunker. Each answerable question lists the facts it needs (all required) and, for each fact, every passage that would do (any one is enough); unanswerable questions list nothing and test whether the system declines. The set mixes question types on purpose, because each type breaks a different stage, and every LLM-drafted item is checked by you before it counts. Once frozen, the set gets a hash, a dev/test/holdout split by group, and a version, so that two runs can only be compared when they used exactly the same questions.

**The theory in one read (11 linked ideas, each with its formula or rule).**
1. *Why a fixed set:* a comparison needs the same questions on both sides: comparison keys = (`dataset_sha256`, `snapshot_id`, qid set, labels, split, `scorer_version`).
2. *The frozen snapshot:* `doc_text = "\n".join(pages)`; `page_table[p] = (start_p, end_p)`; doc offset = `start_p` + page offset.
3. *Why spans, not chunk ids:* a chunk id changes with chunk size; a span `(doc, a, b)` does not.
4. *Evidence groups:* item supported ⇔ ∀ group ∃ alternative fully present. Unanswerable ⇔ `evidence_groups = []`.
5. *Minimal sufficient span:* the shortest text from which a reader can state the fact with no outside knowledge. A unique quote anchors a span but does not prove it is sufficient.
6. *Categories as a coverage grid:* category × page region; each category must appear in at least 2 regions.
7. *Unanswerables done well:* on-topic, plus a plausible same-type distractor (SQuAD 2.0 rule).
8. *Paraphrase groups:* a variant shares its base item's gold and `group`, and so its split.
9. *Leakage rules:* overlap(q, span) = |content words of q ∩ span| / |content words of q|, kept ≤ 0.3 for vocabulary-mismatch items; no questions from chunks; no eval text in any prompt.
10. *Splits and versions:* split by group (~30% dev; the rest divided between test and holdout); any change ⇒ new file ⇒ new sha256.
11. *Label reliability over time:* span IoU = |A ∩ B| / |A ∪ B| (characters); page agreement; a κ bridge (p_o, p_e, κ = (p_o − p_e)/(1 − p_e)), marked "not estimable" when a label has fewer than 5 items.

**Formula-sheet items:**
- page → doc offset;
- the CE preview (link to M2);
- the overlap ratio;
- span IoU;
- κ;
- the comparison-key tuple;
- category minimums (06 §6.2).

**Step-by-step outline (running example: Corpus D, `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`).** Corpus D is the only frozen course corpus today, and 06 §6.7 already holds 10 verified seeds. Corpus T items follow once DEC-3 is chosen.
1. Read the three complaints in Ch22 p.1/19. Run `evalute_rag.py`'s logic in your head: new questions every run, so no number can be compared.
2. Freeze the snapshot. Open page 10 with offsets and find D-002's quote.
3. Turn D-002 into one group and one alternative. Then D-004: one group, two OR alternatives (p.8 and p.23). Then D-005: two AND groups on p.2.
4. Extend D-007's p.10 span until it names the UNFCCC (sufficiency, M-03).
5. Write one tempting unanswerable, D-009 (IPCC year): grep the snapshot, read every page that mentions IPCC, and record the distractor.
6. Write one paraphrase variant, D-002-P1, and compute its overlap ratio.
7. Fill the coverage grid: 7 categories × 3 page regions. Mark the empty cells as explicit gaps.
8. Assign splits by group with a fixed seed. Compute `dataset_sha256`. Change one character and watch the hash change.
9. Seven days later: re-label 20% blind, then compute page agreement, span IoU and (if estimable) κ.

**Visuals that earn their place:**
- **Snapshot-to-span diagram** (SVG): pages → joined text → page table → one span. Shows why offsets need a frozen extractor.
- **Evidence-group tree** for D-004 and D-005: AND above, OR below. Shows the logic CE@k will test.
- **Coverage grid heat map** (category × page region): q_a.json (everything in pp.1–5) beside the planned set. Shows the skew being fixed.
- **Overlap-ratio strip plot** per category. Shows which items silently favour BM25.

**Full only:**
- the loader's fail-closed checks (06 §5.3 rule 4, R-02 negative tests);
- cross-page spans as two segments;
- `grade` for graded nDCG;
- CRAG's extra question types;
- the BEIR hole study;
- the self-agreement thresholds;
- the leakage n-gram test design;
- SQuAD 2.0's negative-type breakdown;
- Corpus T differences (two-column layouts, tables).

### 7. Verify notebook plan

`study/notebooks/M1_evalset_verify.ipynb`, offline, with no API calls. Runtime under 1 minute.
1. Build the Corpus D snapshot with PyMuPDF 1.26.7 (pinned), recompute `snapshot_id`, and check it against 06 §5.3 with `contracts_check.validate_binding`.
2. Load the 10 seed items from 06 §6.7 (copied into the notebook as JSONL). Resolve every quote, assert it occurs once on its page, and convert to doc offsets. Show D-002 → [20993, 21092).
3. Recompute the M-03 sufficiency fixes (D-004 p.23, D-007 p.10/p.29) and show the before and after spans as text.
4. Plot the overlap ratio per seed item (Plotly strip), with D-006 (vocabulary mismatch) as the check.
5. Reproduce the q_a.json page skew: all 44 answers best-match pp.1–5 (the IDF-overlap method, as in §1). Plot the coverage grid beside a planned grid.
6. Assign splits by group with `contracts_check.assign_splits(seed=0)`. Show that D-002-P1 lands with D-002.
7. Hash demo: `dataset_sha256` before and after a one-character edit.
8. Span IoU and κ toys. Include the AE Ch4 trap: two raters both saying "pass" 90% of the time, chosen independently, agree 0.82 by chance (not 0.81). Include the always-same-label case where κ is undefined, so `cohens_kappa` returns None.

### 8. Apply-it tool plan and real-world checklist

`study/tools/evalset_check.py`: "Is my eval set good enough to measure with?"
- **Inputs:** `--docs` (PDF/MD/TXT), `--evalset` (JSONL in the 06 §6.1 schema, or a light form `{q, answer, quote, page, category, answerable}` that the tool upgrades into spans by quote search), optional `--relabel` (a second labelling pass), optional `--bm25` (adds a lexical-ceiling check using P3's tokenizer; no API).
- **Output:** a Markdown report: snapshot binding, per-item resolution, coverage grid, overlap per category, unanswerable audit, split integrity, hash, self-agreement, the checklist verdicts and a recommendation.

**Real-world checklist (12 checks)**

| # | Check | Auto / manual |
|---|---|---|
| C1 | Every quote resolves exactly once on its page in the frozen text | auto |
| C2 | Every span is sufficient: shown alone, a reader can state the fact | manual: read the span aloud with no context; extend it if it uses "it", "this" or a truncated name |
| C3 | Every group lists all sufficient alternatives in the corpus (no holes) | auto (grep for key terms on other pages) + manual (read the hits) |
| C4 | Each category meets its minimum and appears in at least 2 page regions | auto |
| C5 | Vocabulary-mismatch items have overlap ≤ 0.3; the overlap distribution per category is shown | auto |
| C6 | Unanswerables: no answer string anywhere in the corpus, and at least half are tempting | auto (grep) + manual (read every page mentioning the topic) |
| C7 | No item was generated from chunks; LLM items are human-verified (`created_by`) | auto (field check) + manual |
| C8 | Paraphrase variants share `group` and split with their base item | auto |
| C9 | No `split: "unassigned"`; the split is stratified by category; the holdout is untouched | auto |
| C10 | `dataset_sha256` recorded and bound to `snapshot_id` | auto |
| C11 | BM25-only and closed-book ceilings are not near 100% (the set can discriminate) | auto (BM25) + manual (the closed-book result comes from the M3 run) |
| C12 | Self-agreement: page agreement ≥ 0.9, mean span IoU ≥ 0.6, κ reported only when estimable | auto (with `--relabel`) |

**Recommendation logic:**
- C1, C8, C9 or C10 fails → "not loadable: fix before any run".
- C4 or C6 fails → "measurable, but missing categories: write items for the empty cells".
- C5 or C11 fails → "biased toward BM25 / parametric knowledge: rewrite the flagged items".
- C12 fails → "unclear guideline: fix the rubric, re-label the category and bump the version".
- Otherwise → "ready to freeze".

### 9. LLMOps notebook plan

`study/llmops/notebooks/M1_dataset_ops.ipynb`: the eval set as a versioned, mirrored production dataset.
- **Framework build:** no chain is needed. Two framework pieces:
  - (a) a `langsmith` dataset mirror of the frozen Corpus D set, tagged with the first 12 hex digits of `dataset_sha256`, using splits `dev` and `test` (**holdout is never pushed**);
  - (b) optionally, the same as a Phoenix dataset, for the local view.
  - Maps to lesson step 8 (freeze and version).
  - **Default to name:** LangSmith versions a dataset on every change, so the local JSONL stays the source of truth and the mirror is one-way (foundation §4).
- **External calls (cached):**
  - Optional LLM drafting from whole pages: tuples first, then one question per tuple (AE Ch3 method), about 11 page windows × 2 calls ≈ **22 Groq calls** (`openai/gpt-oss-20b`, `reasoning_effort=low`, structured output); alternatively Claude Haiku 5.5.
  - LangSmith uploads only after `privacy.assert_corpus_is("D")` passes.
  - Replay mode serves every draft from `calls.sqlite`, so the notebook reruns with no key.
- **Tracing:**
  - Each drafting call becomes a span with the page window, tuple, prompt version, `cache_key` and token usage.
  - The local JSONL trace is the default; Phoenix is the local viewer; LangSmith only for Corpus D.
- **Dataset and evaluators:**
  - Code checks C1, C4–C10 from §8, wrapped as dataset-level evaluators (`inputs, outputs, reference_outputs → {key, score}`).
  - The **leakage check** from foundation §4: normalised 8-word overlaps between eval items and every prompt and few-shot file.
  - No LLM judge (D-10). There is no "previous version" for M1, so the experiment compares **draft vs human-verified** subsets on BM25-only Hit@4: the inflation that [S23] predicts.
- **Cost / latency / tokens:**
  - About 22 calls × (~2,500 input + ~600 output tokens) ≈ $0.02 on Groq, ≈ $0.03 on Haiku 5.5 ($0.10/$0.50 per 1M) and ≈ $0.23 on Sonnet 5.5 ($2/$10).
  - Rate-limit time is ≥ 7 minutes at 8K TPM (plan **UNVERIFIED**, foundation §6.3).
- **Prompt and config versioning:**
  - `prompts/evalset_tuples_v1.txt` and `prompts/evalset_question_v1.txt`; `datasets/CHANGELOG.md`.
  - Each dataset version links the prompt versions of its drafted items.
- **Monitoring and feedback:**
  - The monitor page (foundation §8.3) shows items per category, the share of drafted items, the share of verified items and the hash history.
  - Alert when a frozen file's hash changes, or when a scored run meets an `unassigned` split.
  - A failure confirmed in M5 enters as a new item in the next MINOR version (`ci-cd-evals`, `error-analysis`).
- **Place in the lifecycle:** Analyze (`synthetic-data-generation`, `error-analysis`), then the start of Measure. dev → CI: the T1 tests for the loader, hash and leakage check.
- **Skills used:** `synthetic-data-generation`, `collaborative-annotation`, `ci-cd-evals`, `llm-observability`.

### 10. Tools, frameworks, libraries and LLMs

**Shared rows for every Phase 3 concept.** M2–M5 below refer back to this table and add only their own rows. Pins are the newest release on or before 2026-10-03, taken from the PyPI JSON API (the M3/M4 helper and `LLMOPS_FOUNDATION.md` §11). "Installed" comes from a read-only `uv pip list`, 2026-10-17.

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| LLM, high-volume steps (item drafting, controls, flip rate) | Groq `openai/gpt-oss-20b` (`GROQ_MODEL_ID`), `reasoning_effort="low"`, explicit `max_completion_tokens`; structured outputs `json_schema` with `strict: true` (verified for this model; no streaming or tool use with it) | `groq` 1.7.0 | yes | no (API); **replay yes** | $0.075 / $0.30 per 1M tokens; 30 RPM / 8K TPM (plan **UNVERIFIED**) | Apache-2.0 | yes (D-04) |
| LLM, optional when credits exist | Claude Haiku 5.5 `claude-haiku-5-5`, effort `low` (never send `temperature`) | `anthropic` 1.11.0 | no | no; replay yes | $0.10 / $0.50 per 1M (prompts ≤ 100K) | MIT | yes (D-32) |
| Comparison generator arm only (not needed in Phase 3) | Claude Sonnet 5.5 `claude-sonnet-5-5` | `anthropic` 1.11.0 | no | no | $2 / $10 per 1M; about $0.45 per 55-question run | MIT | yes (D-32), as an experiment arm |
| Judge, **end batch only** | Cohere `command-a-03-2025` or `command-a-reasoning-08-2025` (verified as live ids). `response_format={"type": "json_object", "schema": …}`, which cannot be combined with `documents`, so the contexts go in the message text. Accepting temperature 0 is **UNVERIFIED** | `cohere` 7.2.0 | yes | no; replay yes | about 165 calls per judged version (06 §8.6); trial cap 1,000 calls/month | MIT | yes (D-10) |
| Embeddings | Cohere `embed-v4.0` (C3 cache) and local `all-MiniLM-L6-v2` | `cohere` 7.2.0; `sentence-transformers` 6.1.0 | yes | MiniLM yes | Cohere per call (price **UNVERIFIED**) | MIT / Apache-2.0 | yes (D-03) |
| Framework core | `langchain-core` (retriever wrapper, LCEL, evaluator signatures) | 1.6.6 | no | yes | — | MIT | yes, after the mechanism (D-32) |
| Graphs | `langgraph` | 1.2.12 | no | yes | — | MIT | **not needed in Phase 3**: no branches or cycles |
| Provider integrations | `langchain-groq` 1.1.3 / `langchain-cohere` 0.6.0 **not used**: they conflict with groq 1.7 and cohere 7.2. Use the foundation's `CachedChatModel` and `CachedEmbeddings` adapters; `langchain-anthropic` 1.7.5 is optional | — | no | — | — | MIT | adapters yes |
| Hosted tracing, datasets, eval | `langsmith`. **Defaults that upload:** `evaluate(upload_results=True)`; the auto-registered pytest plugin uploads unless `LANGSMITH_TEST_TRACKING=false` | 0.14.4 (latest 0.14.11) | no | SDK partly (`upload_results=False` is beta; running with no key at all is **UNVERIFIED**) | free plan | MIT (SDK) | yes, **Corpus D only** |
| Local tracing | `arize-phoenix-otel` + `openinference-instrumentation-langchain` / `-groq`; the Phoenix server via `uvx arize-phoenix@20.19.0 serve` | 0.17.2 / 0.1.78 / 0.1.31 | no | yes | $0 | Apache-2.0 (client), ELv2 (server) | yes |
| Cache and replay | `study/llmops/` helper package (plan; foundation §10) | — | not built | yes | — | ours | required (D-32 (7)) |
| Tests and local CI | `pytest`, `pre-commit`, `nox` | 9.1.1 / 4.6.2 / 2026.8.17 | pytest yes | yes | — | MIT / MIT / Apache-2.0 | yes |

**M1's own rows**

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Frozen snapshot, page offsets | `pymupdf` | ==1.26.7 (pinned) | yes | yes | — | AGPL-3.0 | yes (pinned by decision) |
| Eval-set schema validation | `jsonschema` (Draft 2020-12), or `pydantic` models | 4.26.0 / 2.13.5 | yes / yes | yes | — | MIT / MIT | yes |
| BM25 lexical-ceiling check | `rank-bm25` (P3 tokenizer) | 0.2.2 | yes | yes | — | Apache-2.0 | yes |
| Overlap and token counts | `tiktoken` (`o200k_harmony`) | 0.14.0 | yes | yes | — | MIT | yes |
| Optional drafting of candidate items | Groq gpt-oss-20b (structured output), or Haiku 5.5 | — | — | replay yes | about 22 calls ≈ $0.02 (Groq), $0.03 (Haiku), $0.23 (Sonnet) | — | yes; whole pages only, human-verified |
| Read only | `ragas` testset generator (knowledge-graph transforms, query synthesizers) | 0.4.3 | no | — | LLM calls with OpenAI defaults | Apache-2.0 | **no** (OpenAI defaults, telemetry, generates from chunks) |

**Install lines** (do not run): none for the M1 core. LLMOps: `uv add --group llmops langsmith==0.14.4 langchain-core==1.6.6 arize-phoenix-otel==0.17.2`.
**Keys:** `GROQ_API_KEY` and `COHERE_API_KEY` are present. Add `ANTHROPIC_API_KEY` and `LANGSMITH_API_KEY` (+ `LANGSMITH_ENDPOINT`) only when needed. Never put `LANGSMITH_TRACING` in `.env`.

### 11. Open questions for Yash (preferences only)

- Read the AE sections next to Ch22 (about 30–40 minutes), or only the two that change what you do? **read / pieces** (open since the 2026-10-09 review, question 3).
- Should LLM drafting use a **different model family** from the generator (Claude Haiku 5.5 when you have credits), to avoid questions shaped by gpt-oss's own phrasing? This is an inference, not an established effect. **yes / no**

---

## Concept M2: Retrieval metrics harness

### 1. Sources checked

- **Book (verified):**
  - Ch22 p.4/19: LLM-judged context relevance; Precision@K, with the 3-of-5 = 0.6 example.
  - Ch22 p.4–5/19: Recall@K over all relevant documents (3 of 10 = 0.3); rank-aware context precision.
  - Ch22 p.5–6/19: MRR, MAP and NDCG, with graded relevance.
  - Ch22 p.7/19: the ranking-quality picture.
  - Ch22 p.13/19: component-level metrics isolate the retriever.
- **Repo (verified):**
  - No rank metric anywhere (04 DV-43 stands).
  - `define_evaluation_metrics.ipynb` cells 9–11: an LLM-judged context score. Cell 9 has a NameError on static reading. The scale is graded 0 / 0.33 / 0.66 / 1, not a ratio. Cell 11's saved output is stale (§4).
- **Course files:**
  - 02 M2 card; 03 §6.1–6.4; 04 M2 row.
  - 06 §7.1–7.3 (definitions, the toy table, the traps), §7.6, §9.6 (T1 tests).
  - P6 lesson (headings: CE@k only in §D.7 "Preview only"; Group-Recall only in a Part E row; Span-Coverage absent).
  - `contracts_check.py` functions `ce`, `group_recall`, `span_coverage`, `rel` and `complete_evidence`.
- **AE book:**
  - AE Ch7, 'Overview', 'Precision@k and Recall@k', 'Mean Reciprocal Rank (MRR)', 'Normalized Discounted Cumulative Gain (NDCG@k)', 'Common Pitfalls'.
  - AE Ch5, 'Optional: Group-wise Metrics for Evaluating Multiple Outputs' (its Success@k is our Hit@k).
- **Interview repo:**
  - AIQ 07 Q22 (component vs end-to-end), Q23 (known error: calls hit rate "Recall@k"; already seed S5, so do not reuse).
  - AIQ 04 Q43, Q53.
- **External:** [S16] BEIR · [S17] Chroma (token-level IoU) · [S11] RAGChecker (claim-level retriever metrics) · [S24] Know Your RAG (per-category recall gaps).

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Ranked list, top-k, qrels | everywhere | P2, P6 (written, not studied) | P2/P6 | no | bridge | Three-line refresher with one ranked list |
| 2 | Precision@k, Recall@k (document-level, as in the book) | Ch22 p.4–5/19 | P6 (not studied) | P6 | no | bridge | Book numbers first (0.6, 0.3), then why "all relevant documents" is undefined for chunks |
| 3 | Hit@k, MRR, nDCG@k with IDCG over all relevant chunks | 06 §7.3 | P6 (not studied) | P6 | exposed (M2, O1) | bridge | The toy table from 06 §7.3, recomputed |
| 4 | **MAP** | Ch22 p.6/19 | P6? (not checked in body) | P6 | no | bridge | One line: AP is "context precision@k" in 06's average-precision form; MAP is its mean over questions |
| 5 | Chunk relevance from spans (`any_overlap`, ≥ 1 non-whitespace character) | 06 §7.2 | 06 only | M2 | no | core | Two chunks and one span, drawn |
| 6 | Coverage over the **union** of chunk ranges; whitespace-only tolerance | 06 §7.2 | 06 only | M2 | no | core | The span split across two chunks (CE = 1) |
| 7 | **CE@k**, Group-Recall@k, Span-Coverage@k | 06 §7.2–7.3 | P6 previews CE only | M2 | no | core | The D-005 fragment counterexample (Hit = 1, CE = 0); the toy CE@3 = 0, CE@5 = 1 |
| 8 | First evidence vs sufficient evidence | 03 §6.2 | 06/03 only | M2 | no | core | The central idea of the lesson |
| 9 | Metrics over answerable items only; macro average; n beside every number | 06 §7.6 | 06 only | M2 | no | core | Rule box |
| 10 | Overlap makes Precision@k and nDCG reward redundancy; IDCG changes with chunk size | 06 §7.3 traps | 06 only | M2 | no | core | Show two overlapping chunks both counted relevant |
| 11 | CE at three stages: candidate pool, final top-k, final context | 03 §6.2; v4.x | 03 only | M2 (X3 uses it) | no | core | Diagram; final-context CE is "next" for v4 |
| 12 | Context tokens retrieved; CE@k vs tokens (the k trade-off, MC-005) | 06 §7.3; MC-005 open | C4 lab (not studied) | M2 | no | core | k-sweep curve: CE@k against mean context tokens (closes part of MC-005) |
| 13 | Determinism: tie-break by `chunk_id`; bit-identical reruns | 02 M2 Evidence; MX-2 | C4 (not studied) | M2 | no | core | Show a tie and the sort key; the T1 determinism test |
| 14 | LLM-judged context relevance cannot see what was never retrieved | Ch22 p.4/19; 03 §6.2 | 03 only | M2 | no | core | Contrast the repo cells 9–11 with label-based CE |
| 15 | Per-category reporting; n = 4–10 gives anecdotes | 06 §7.3, §9.4 | 06 only | M2 | no | core | Per-category table with n; link to M4 |
| 16 | Hubness: chunks retrieved often but rarely gold | ext review §4 M2 | **missing** | M2 | no | core (Full) | Diagnostic task, not a metric |
| 17 | The 2×2 of retrieval × answer outcome | 03 §6.3 | 03 only | M3/M5 | no | next | Link; M3 and M5 teach it |
| 18 | Unit tests from hand-computed toys; regression thresholds | 06 §9.6 | 06 only | M4 | no | next | M2 writes the metric tests; M4 owns the regression test |
| 19 | Token-level IoU as an alternative span metric | [S17] | **missing** | M2 | no | core (Full) | One paragraph: IoU penalises redundant tokens; CE asks "is it all there"; they answer different questions |
| 20 | Claim-level retriever metrics (RAGChecker claim recall) | [S11] | **missing** | M2 | no | next | Link only; they need a judge (D-10) |

### 3. Quiz coverage

There is no question file. Needed titles:
- **R:** Why can Hit@4 = 1 while CE@4 = 0? · What does IDCG divide by, and why does it change with chunk size? · Why are retrieval metrics computed only over answerable items?
- **A:** Compute Hit@3, CE@3, CE@5, Group-Recall@3, RR and binary nDCG@5 for the ranked list `[c5, c3, c9, c7, c1]` (06 §7.3 toy). · Two chunks cover [0, 50) and [40, 95) of a span [10, 90): is the alternative satisfied? · A tie at rank 4: which chunk wins, and why must the rule be fixed?
- **T:** Hit@4 is 0.95 but answers are often wrong: where do you look first? (CE@4, then the generator, then traces; ext review §4 M2.) · A teammate reports nDCG@10 for two chunkers with different chunk sizes: what is misleading?
- **Interview:** AIQ 04 Q43, "What retrieval metrics would you track - recall@k, MRR, nDCG - and what does each actually tell you?" Second choice: AIQ 04 Q53 on harness design.

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| M2-E1 | 02 M2 Repo line; 03 §6.2 row "Context relevance by LLM judge" | `define_evaluation_metrics.ipynb` cell 9 scores 0 / 0.33 / 0.66 / 1 per chunk and averages, so it is not a "fraction of useful chunks" (Ch22 p.4/19). Cell 11's saved 1.0 cannot come from the current code (NameError in cell 9) | Describe it as a graded, averaged judge score with a stale output |
| M2-E2 | 06 §7.3 metric list | Omits MAP, which the book teaches (Ch22 p.6/19); 06's "context precision@k" is AP restricted to the retrieved relevant chunks | Add one row "MAP = mean AP (diagnostic)", or say the omission is deliberate |
| M2-E3 | P6 (headings) | Span-Coverage is not mentioned and Group-Recall appears only in a Part E row, while M2 uses both as diagnostics | M2 must teach both from scratch (no P6 edit needed) |
| M2-E4 | AE Ch7 'Normalized Discounted Cumulative Gain (NDCG@k)' | IDCG re-sorts only the retrieved documents, the formula has a typo (log2(23) for log2(3)), and the prose disagrees with the formula (AE helper; also ext review §8) | Lessons use 06's IDCG; the AE section is a critique target only |
| M2-E5 | `.claude/skills/rag-evaluation` | Defines Recall@k at document level only, with no sufficiency metric | Lesson note only |

### 5. What the research says

- **Document-id labels cannot follow re-chunking.**
  - *Study:* BEIR evaluates 18 datasets with id-keyed qrels and nDCG@10 [S16].
  - *Result:* the metric works across binary and graded labels. The label pools were built from lexical systems, so dense systems were under-credited until the holes were judged (+8.1 nDCG points for ANCE).
  - *What it means:* a metric is only as fair as its labels.
  - *For your project:* CE@k on spans is chunker-independent, but list all alternatives (M1 #20) to keep holes small.
- **Token-level span metrics are the closest published practice.**
  - *Study:* Chroma (2024) scored chunkers by token precision, recall and IoU against exact excerpts, at k = 5 over 472 queries [S17].
  - *Result:* recall differed by up to about 9% between strategies. Overlap hurt IoU, because duplicated tokens count against precision.
  - *For your project:* same idea as Span-Coverage. CE adds the all-or-nothing sufficiency rule that IoU lacks.
- **Averages hide categories.** Recall@5 varied by 4.8–42 points across question types in Know Your RAG [S24], so report per category.
- **Claim-level retriever metrics exist,** for example RAGChecker's claim recall: gold claims found in the retrieved chunks [S11]. They need an LLM to extract and check claims, so they wait for the end batch.
- **Current practice:**
  - two-stage evaluation, with recall for candidate generation and nDCG or MRR for ranking (AE Ch7, 'Overview');
  - always report n;
  - cross-check metric code against a reference library.
- **Pitfalls:**
  - non-standard IDCG (AE Ch7);
  - Recall@k mistaken for hit rate (AIQ 07 Q23, a known repo error);
  - LLM-judged relevance scores that cannot see missed evidence;
  - nDCG compared across chunk sizes.
- **Interview questions:**
  - Which retrieval metrics, and when? (AIQ 04 Q43)
  - Why evaluate components separately? (AIQ 07 Q22)
  - Design a harness that blocks merges (AIQ 04 Q53).
  - Why can recall be high and answers still wrong?

### 6. Lesson blueprint

**The answer first.** A retrieval metric looks only at the ranked list of chunks and compares it with the gold spans, so it needs no LLM and gives exactly the same number on every rerun. Hit@k, MRR, Precision@k and nDCG ask whether *some* evidence arrived, and how early. Complete-Evidence@k asks the question that matters for an answer: did every required fact arrive in full, in the union of the top-k chunks? Because the gold is a span, the same score works for any chunker, and two chunks can jointly cover a fact that a boundary cut in half. The harness reports CE@k as the primary number, the others as diagnostics, everything per category with its n, and it must give bit-identical results on a rerun.

**The theory in one read (10 ideas).**
1. *Ranked list:* R_k = (c_1 … c_k); ties broken by `chunk_id`.
2. *Relevance from spans:* rel(c) = 1 ⇔ c overlaps ≥ 1 non-whitespace character of any gold segment.
3. *First-evidence metrics:* Hit@k = 1[∃ i ≤ k: rel(c_i)]; RR = 1/rank of the first relevant chunk (0 if none); Precision@k = Σ rel / k.
4. *Ranking quality:* DCG@k = Σ (2^g_i − 1)/log2(i + 1); nDCG = DCG/IDCG over all relevant chunks in the index. AP = Σ P@i·rel_i / #relevant retrieved; MAP = mean AP.
5. *Coverage on the union:* U = ∪ ranges of the chunks in the stage's set.
6. *Alternative satisfied:* every non-whitespace character of its segments ∈ U. Group satisfied: at least one alternative is.
7. *CE@k* = 1[every group satisfied]; *Group-Recall* = satisfied groups / groups; *Span-Coverage* = mean over groups of the best alternative's covered fraction.
8. *Why sufficiency differs from first evidence:* the D-005 fragments give Hit = 1 and CE = 0.
9. *Stages:* CE@pool ≥ CE@k ≥ final-context CE when assembly only removes text.
10. *Reporting:* macro average over answerable items, per category with n, plus mean context tokens.

**Formula sheet:** Hit@k, RR/MRR, Precision@k, AP/MAP, DCG/IDCG/nDCG, rel(c), CE, Group-Recall, Span-Coverage, and the reporting rule.

**Step-by-step outline (running example: Corpus D seeds D-001…D-008 with v0's dense retrieval).**
1. Recompute the 06 §7.3 toy table by hand: `[c5, c3, c9, c7, c1]`.
2. Draw D-005's two spans on page 2 and the 1000/200 per-page chunks. Find which chunks overlap.
3. Retrieve top-4 for D-005 with MiniLM (offline). Compute rel, Hit@4, CE@4 and Group-Recall@4.
4. Show the fragment counterexample (06 §9.6 `test_sufficiency_contract`).
5. Show the union rule: shift chunk boundaries so that one span is split across two retrieved chunks, giving CE = 1.
6. Run all 8 answerable seeds. Fill the per-category table with n.
7. Sweep k = 1…10. Plot CE@k and mean context tokens (MC-005).
8. Rerun and diff: identical, then break the tie rule and watch it differ.

**Visuals:**
- **Span-and-chunks ruler** (SVG): character axis, gold span bars, chunk bars, union shading. Shows rel vs CE at a glance.
- **First-evidence vs sufficiency matrix:** each seed item × {Hit@4, CE@4}. Shows items with Hit = 1 and CE = 0.
- **k-sweep chart** (Plotly): CE@k and context tokens against k. Shows the trade-off behind MC-005.
- **DCG discount curve** (from the formula): rank 2 keeps 63%, rank 10 keeps 29%. Shows why order matters.

**Full only:**
- graded nDCG with `grade`;
- the IDCG trap across chunkers;
- CE at the pool and final-context stages;
- token-level IoU (Chroma);
- hubness;
- MAP vs context precision;
- the AE IDCG critique;
- the ranx cross-check.

### 7. Verify notebook plan

`study/notebooks/M2_retrieval_metrics_verify.ipynb`, offline by default.
1. Recompute every row of the 06 §7.3 toy table. Assert equality with `contracts_check` and with the cross-check library (`ranx` or `ir-measures`, test group).
2. Corpus D snapshot (as in M1) → 1000/200 per-page chunks (C2 parameters) → MiniLM `all-MiniLM-L6-v2` embeddings (local cache, `HF_HUB_OFFLINE=1`) → exact cosine top-k with the `chunk_id` tie-break.
3. Score D-001…D-008 at k = 1…10: Hit, RR, Precision, nDCG, CE, Group-Recall, Span-Coverage, plus context tokens (tiktoken `o200k_harmony` and MiniLM WordPiece, both named).
4. Charts: span-and-chunks ruler for D-005; the Hit vs CE matrix; the k-sweep (Plotly).
5. Determinism: two runs, `hashlib` of the metric JSON identical; then a tie-break ablation to show non-determinism.
6. Optional cell: the same with the **cached** Cohere `embed-v4.0` index from C3. It runs in replay mode only; no new call unless Yash records.
7. BM25 column (P3 tokenizer) for D-008 (Kigali, a rare term), to show an exact-term item failing dense and passing lexical.

API calls: none (Cohere optional, cached). Runtime about 1–2 minutes on CPU.

### 8. Apply-it tool plan and real-world checklist

`study/tools/retrieval_eval.py`: "How well does my retriever find the evidence for my questions?"
- **Inputs:** `--docs`; `--evalset` (M1 format, or the light `expect` form used by `bm25_fit_check.py`); `--retriever bm25|minilm|cohere-cached|all`; `--chunk-size --overlap --scope per_page|cross_page`; `--k 1..20`.
- **Output:**
  - a per-item table (rank of first evidence, CE, which group is missing);
  - per-category metrics with n;
  - the k-sweep;
  - a determinism check;
  - a hubness list;
  - the checklist and a recommendation.

**Real-world checklist (11 checks)**

| # | Check | Auto / manual |
|---|---|---|
| C1 | Metrics are over answerable items only, and n is printed per category | auto |
| C2 | CE@k is reported as primary; Hit/MRR/nDCG are labelled diagnostics | auto |
| C3 | Two runs give identical metrics (tie rule set) | auto |
| C4 | No item has Hit@k = 1 and CE@k = 0 unexplained: each such item shows which group is missing | auto (list) + manual (read) |
| C5 | Chunks are not truncated by the embedder's max length (MiniLM 256 tokens) | auto |
| C6 | CE@k at the chosen k is close to CE@pool (otherwise ranking, not recall, is the problem) | auto |
| C7 | The k you plan to use is justified by the CE@k vs tokens curve | auto (curve) + manual (choose) |
| C8 | No category has fewer than 4 items (otherwise it is marked "anecdote") | auto |
| C9 | Hub chunks (retrieved for more than 3× the even-spread rate, rarely gold) are listed | auto + manual (read them) |
| C10 | Exact-term items are checked with BM25 too | auto |
| C11 | Metric code matches the reference implementation on the toy table | auto |

**Recommendation logic:**
- C3 or C11 fails → "harness not trustworthy".
- CE@pool low → "recall problem: candidate generation or chunking (Phase 4/5 cards)".
- CE@pool high but CE@k low → "ranking problem: reranking (R3)".
- Exact-term items fail dense and pass BM25 → "hybrid (R1)".
- C5 fails → "chunks too long for the embedder".

### 9. LLMOps notebook plan

`study/llmops/notebooks/M2_retrieval_eval_ops.ipynb`: retrieval evaluation as it runs in a team.
- **Framework build:**
  - A `langchain-core` `BaseRetriever` wrapper over the course's NumPy index, returning `Document`s whose metadata includes `chunk_id`, `doc_id`, `char_start`, `char_end` and `score`. Maps to the retrieve step.
  - **Defaults to name:** `VectorStoreRetriever` uses `k=4` and similarity search (foundation §9.2). The wrapper takes k from the config. LangChain retrievers return `Document`s without offsets unless you put them in metadata, and CE needs offsets.
- **Evaluators:**
  - CE@4, Group-Recall@4, Span-Coverage@4, Hit@4, RR and nDCG@10 as code evaluators with the `(inputs, outputs, reference_outputs) → {key, score}` signature.
  - Run through `langsmith.evaluate(target, data=…, evaluators=[…], upload_results=False)` and through the course runner. The two must give identical numbers.
- **External calls (cached):**
  - Cohere `embed-v4.0` for the queries: about 50 queries, one or two batched calls, through `CachedEmbeddings`. Document vectors come from the C3 cache (no new calls).
  - MiniLM runs locally.
  - Replay serves everything.
- **Tracing:**
  - A retriever span per query with OpenInference `retrieval.documents` (id, score, rank) and the metric results as span attributes.
  - Exported spans carry chunk ids and scores, never chunk text, unless the corpus is D (foundation §3.3).
- **Dataset:** the M1 mirror (`dev` only for iteration).
- **Experiment against the previous version:**
  - v0 against a v0 rerun (the determinism test: must be bit-identical).
  - v0 MiniLM against v0 Cohere (a diagnostic only, not an adoption decision).
- **Cost / latency:**
  - Retrieval p50/p95 per stage (embed query, search) with the percentile method named.
  - Embed cost per 1,000 queries (Cohere price **UNVERIFIED**, foundation §6.2).
- **Versioning:** `config.yaml` with `k`, `params_hash` and `embed_hash`. `scorer_version: s1` goes into every result.
- **CI and monitoring:**
  - T1 tests: the toy table, the sufficiency contract, page→doc conversion, determinism, and retrieval regression on the frozen set with cached vectors.
  - Monitor: CE@4 per version and per category; the hub list; an alert when CE@4 drops below the champion minus the tolerance, or when the per-qid flip list is non-empty.
- **Lifecycle:** Measure. dev → CI: the T1 retrieval suite starts here (v0.1).
- **Skills:** `rag-evaluation`, `code-based-evaluators`, `ci-cd-evals`, `llm-observability`, `trace-data-analysis`.

### 10. Tools, frameworks, libraries and LLMs

The shared rows are in M1 §10. M2's own rows:

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Exact search, metrics | `numpy` | 2.5.3 | yes | yes | — | BSD-3 | yes (D-07) |
| Offline embedder | `sentence-transformers/all-MiniLM-L6-v2` (256-token limit) | `sentence-transformers` 6.1.0 | yes (HF cache) | yes (`HF_HUB_OFFLINE=1`) | $0 | Apache-2.0 | yes |
| Metric cross-check (T1) | `ir-measures` + `pytrec-eval-terrier`: `Success@k` = Hit@k, `RR`, `nDCG@k`. **Gain caveat:** pytrec_eval's nDCG gain is linear by default; ours is 2^g − 1. Identical for binary labels; set a custom `gains` map for graded ones | 0.4.3 + 0.5.10 | no | yes | — | Apache-2.0 + MIT | yes (dev group); cp312 win_amd64 wheel |
| Second choice for the cross-check | `ranx` (`ndcg` is linear; `ndcg_burges` is exponential) | 0.3.21 | no | yes | — | MIT | heavier: numba and ir-datasets, 39 packages |
| Quick nDCG check | `sklearn.metrics.ndcg_score` | 1.9.1 | yes | yes | — | BSD-3 | yes |
| Charts | `plotly` | 7.1.0+ | yes | yes | — | MIT | yes |
| Query embeddings for the LLMOps view | Cohere `embed-v4.0` via `CachedEmbeddings` | — | — | replay yes | about 1–2 batched calls for ~50 queries | — | yes |
| Read only | TruLens `GroundTruthAgreement` (ndcg, precision, recall, mrr, hit rate) | 2.14.0 | no | — | — | MIT | no: 152 packages with the dashboard |

**Install line** (do not run): `uv add --group dev ir-measures==0.4.3 pytrec-eval-terrier==0.5.10`.
**Keys:** none for the default path (MiniLM). The Cohere path is replay-only from the C3 cache.

### 11. Open questions for Yash (preferences only)

- Use the second embedder (cached Cohere) in the verify notebook as well as MiniLM, or MiniLM only (fully free and offline)? **both / minilm**

---

## Concept M3: Generation metrics and LLM-as-judge

### 1. Sources checked

- **Book (verified):**
  - Ch22 p.2–4/19: the evaluation triad.
  - Ch22 p.7–8/19: faithfulness by claims, with the algorithm sketch on p.8.
  - Ch22 p.8/19: sampling-based consistency checking.
  - Ch22 p.8–9/19: answer relevance (reverse-generated questions or direct judging).
  - Ch22 p.9/19: completeness, by weighted sub-questions or reference claims.
  - Ch22 p.9–10/19: why judges work; the four practices; the biases.
  - Ch22 p.10/19: BLEU, ROUGE and BERTScore.
  - Ch3 p.6/14: the hallucination check as a different question from relevance grading.
  - Ch3 p.10–11/14: small models for binary checks; "I don't know" preferred.
- **Repo (verified):**
  - `define_evaluation_metrics.ipynb` cells 3 and 6–8.
  - `evaluation_deep_eval.ipynb` cells 2, 4, 6 and 9 (GEval correctness with gpt-4o; Faithfulness and ContextualRelevancy with gpt-4).
  - `end-2-end_rag_evaluation.ipynb` cells 12, 14, 19 and 22.
  - `evaluation_grouse.ipynb` cells 13–39.
  - `open-rag-eval-example.ipynb` cells 7–14.
  - Discrepancies are in §4.
- **Course files:**
  - 02 M3 card; 03 §5 rows 5, 7, 13 and 14 and the structured-output note; 04 M3 row and the Ch22 table.
  - 06 §3.3 (abstention string), §7.1 (the 2×2 and the closed-book control), §7.4 (definitions and toys), §8 (judge protocol, D-10).
  - 08 D-10, D-22; `misconception_log.md` MC-006.
  - `contracts_check.py` functions `wilson`, `cohens_kappa` and `kappa_bootstrap`.
- **AE book:**
  - AE Ch5, 'Defining the Right Metrics (What to Measure)', 'Implementing Metrics (How to Measure)', 'Writing LLM-as-Judge Prompts', 'Data Splits for Designing and Validating LLM-as-Judge', 'Iterative Prompt Refinement for the LLM-as-Judge', 'Estimating True Success Rates with Imperfect Judges'.
  - AE Ch7, 'Evaluating Generation Quality'.
  - AE Ch4, 'Measuring Inter-Annotator Agreement' and its subsections.
  - AE Ch10, 'Selecting Traces for Human Review', 'Features That Improve Review Speed and Quality'.
  - AE Ch2, 'Absolute Evaluation'.
- **Interview repo:**
  - AIQ 07 Q5, Q10, Q15–Q18, Q24, Q30.
  - AIQ 04 Q44, Q60.
  - `12-coding-challenges/12_eval_metrics.py` (normalize, EM, F1; **decimals not protected**).
  - harvey.md Q2.
- **External:** [S1] RAGAS · [S2] ARES · [S3] MT-Bench · [S4] Wang et al. · [S5] FActScore · [S6] ALCE · [S7] SQuAD + official evaluate-v2.0.py · [S8] Panickssery et al. · [S9] Judging the Judges · [S10] EvalGen · [S11] RAGChecker · [S12] TREC 2024 nuggets · [S13] judgy · [S14] SelfCheckGPT · [S22] RGB.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | The triad: context relevance, faithfulness, answer relevance | Ch22 p.2–4/19 | **missing** | M3 | exposed | core | Triangle diagram; each edge has one metric |
| 2 | Correctness (vs gold) ≠ faithfulness (vs retrieved context); the 2×2 | 06 §7.1; 03 §6.3 | 03/06 only | M3 | exposed | core | D-003: faithful to the p.6 distractor but wrong; parametric answers are correct but unfaithful |
| 3 | Reference-based vs reference-free | ext review §4 M3; AE Ch2 | **missing** | M3 | no | core | Sort the 06 §7.4 metrics into the two kinds |
| 4 | EM and token F1 with SQuAD normalisation; aliases; lenient containment | 06 §7.4 | 06 toy only | M3 | no | core | Write the normaliser from the official script [S7], then fix the decimal trap |
| 5 | **Decimal and thousands trap** ("1.2" → "12") | 06 §7.4; D-001 gold | **missing** (ext review §7 row 11 not yet applied) | M3 | no | core | Show the official SQuAD and AIQ normalisers giving EM = 1 for "12 degrees" vs "1.2 degrees" |
| 6 | Claim decomposition and claim support | Ch22 p.7–8/19 | **missing** | M3 | no | core | Hand-split one v0 answer into atomic claims; label each |
| 7 | Faithfulness ignores omissions; completeness is separate | Ch22 p.9/19; [S5] | **missing** | M3 | no | core | FActScore says it measures precision, not recall [S5] |
| 8 | Answer relevance (reverse questions, or direct judging) | Ch22 p.8–9/19 | **missing** | M3 | no | core (short) | RAGAS method [S1]; human-labelled in the pilot until D-10 |
| 9 | Citation precision and recall (ALCE), and page-hit as a cheap proxy | 06 §7.4 | 06 only | M3 (V1 later) | no | core | ALCE definitions [S6]; page-hit checks the *place*, not *support* |
| 10 | Abstention precision, recall, F1 and false-abstention rate; the fixed string | 06 §3.3, §7.4 | C5 (written, not studied) | M3 (V3 later) | no | core | The 06 toy (P = 0.636, R = 0.700) |
| 11 | Sampling-based consistency (SelfCheckGPT) | **Ch22 p.8/19** | **missing, no owner** | M3 → V4 | no | bridge | One paragraph [S14]; it needs repeated samples, so it links to M4's flip-rate data; detection belongs to V4 |
| 12 | BLEU, ROUGE, BERTScore | Ch22 p.10/19 | **missing** (04 marks it optional) | M3 | no | core (Full) | Why they are brittle for paraphrases; not used for decisions |
| 13 | LLM-as-judge: why it works, the four practices, the biases | Ch22 p.9–10/19 | **missing** | M3 | exposed | core | Evidence numbers in §5 |
| 14 | **Structured LLM output**: schema, enum labels, validation, retry on a parse failure | 03 note; 08 D-22 (recommends M3) | **missing** | M3 | no | core | JSON Schema plus Groq structured outputs; "schema-valid is not correct" (AE Ch8, as in ext review §4) |
| 15 | Human labelling units: claim, citation, answer; abstentions excluded | 06 §8.4 | 06 only | M3 | no | core | Unit table with one example each |
| 16 | Pilot vs certification; disjoint sets | 06 §8.4; D-10 | 06 only | M3 | no | core | Why 30 labels are a rubric pilot (ARES needs ~150 [S2]) |
| 17 | Rubric written after seeing outputs (criteria drift) | ext review §4 M3; [S10] | **missing** | M3 | no | core | EvalGen finding [S10]; re-label the early pilot units when the rubric freezes |
| 18 | κ (p_o, p_e), percent agreement under skew, prevalence | 06 §8.4 | **missing** (used in M1 first) | M3 | exposed | core | Hand 2×2; the "always says supported" checker (agreement 0.90, κ = 0) |
| 19 | TPR / TNR (pass-keep / failure-catch); which class is positive | 06 §8.4; AE Ch5 | **missing** | M3 | no | core | Fix the convention once: Pass = positive, so TNR = failure-catch (ext review §4 M3) |
| 20 | Wilson interval for rates; cluster bootstrap when units share an answer | 06 §8.4 | **missing** | M3 (M4 reuses it) | no | core | Wilson formula; 8/10 → 0.49–0.94 (checked) |
| 21 | Corrected success rate θ̂ and its bootstrap (end batch) | 06 §8; judge-validation skill | **missing** | M3 → end batch | no | core (Full) | Formula only; the run happens at the end. Note that judgy holds p_obs fixed [S13] |
| 22 | Closed-book, oracle-context and context-swap controls | 06 §7.1; ext review §7 row 23; AE Ch7 | 06 (closed-book only) | M3 | no | core | What each control isolates (floor, ceiling, ignoring the context) |
| 23 | MC-006: uncalibrated LLM scores and thresholds | misconception log | open | M3 | exposed (wrong) | core | The remediation the log asks for: pilot labels, choosing on dev, repeat runs ≠ calibration |
| 24 | Which ~10 answers to read per version | 06 §4.1 rule 6; ext review §7 row 19 | **missing** | M3 | no | core | AE Ch10: random answers give the only honest rate; 5 fixed-seed dev qids plus up to 5 flipped items |

### 3. Quiz coverage

There is no question file. Needed titles:
- **R:** Why can an answer be faithful but wrong? · What does citation page-hit check, and what does it miss? · Name three judge biases and one mitigation for each.
- **A:** Token F1 for gold "2015" vs "It was adopted in 2015." · Abstention P/R/F1 from given counts (06 toy). · A checker always says "supported", and 10 of 100 claims are unsupported: agreement, κ, and failure-catch rate? (ext review ★item.) · Wilson 95% interval for 8 of 10.
- **T:** "Every claim is supported, but half the facts are missing. What is faithfulness? Which metric catches the gap?" (★item). · The judge and your labels disagree on 6 of 30 answers: name two causes other than the judge (rubric drift, a label error). · MC-006 check: choosing a 0.7 threshold for an LLM grader on a new corpus.
- **Interview:** AIQ 07 Q17, "How do you decide whether to trust your LLM judge? Walk me through calibration." Second choice: AIQ 04 Q44 (faithfulness, relevance, citations).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| M3-E1 | 02 M3 Repo line, `define_evaluation_metrics.ipynb` cell 3 | The correctness judge is **continuous 0–1**, not binary. Cell 7 returns `result.explanation`, but the field is commented out in cell 2 (an AttributeError on static reading). Cells 8 and 11 have saved outputs that the current code cannot produce (stale) | Describe it as a continuous judge with stale outputs; use cells 3 and 6 as critique targets |
| M3-E2 | 04 Ch22 table row 4 "Answer relevance → `evaluation_grouse.ipynb` cells 13–23" | Cells 13–23 cover **all** GroUSE metrics; answer relevance is cells 13 and 15 only | "cells 13, 15 (answer relevancy); 17 completeness; 19 faithfulness; 21 usefulness" |
| M3-E3 | 04 V4 row / 02 V4 card (`open-rag-eval-example.ipynb` cells 7–14) | Cells 8–14 print `scored_results[0].scores`, the first result rather than the matched query, so the displayed scores may belong to another query (static reading). HHEM appears only in cell 5's saved stderr ("HHEMv2"), never in code | Add the bug; "HHEM" can be cited as "named only in a log line" |
| M3-E4 | 02 M3 card "Book" list | Omits Ch22 p.8/19 (sampling-based consistency) and p.10/19 (reference text metrics) | Add both, as bridge/Full items (§2 #11, #12) |
| M3-E5 | 06 §8.4 decision rule; D-10; 04 M3 row | Certification uses the κ lower bound ≥ 0.40 and failure-class recall only. AE recommends class-wise rates for judges and κ for human–human (AE Ch4 NOTE in 'When to Use Other Metrics'). There is no pass-keep (TPR) bound, so a judge that flags most good answers can still pass (ext review §7 row 12 gives the arithmetic). [S9] shows agreement measures hiding 10-point gaps | Certify on Wilson lower bounds of **both** failure-catch (TNR) ≥ 0.70 and pass-keep (TPR) ≥ 0.70 [P]; report κ only. **(D)**: Codex re-review |
| M3-E6 | 06 §8 end batch; judgy | judgy's bootstrap resamples only the labelled test pairs and **holds p_obs fixed** [S13]; AE's code also has no seed and silently drops degenerate resamples (AE helper) | In the end batch, also resample the unlabelled traces by answer cluster, fix the seed, and report the number of dropped resamples (ext review §7 row 15h) |
| M3-E7 | 06 §7.4 "normalize numbers and units" | Not specified. The official SQuAD script and AIQ `12_eval_metrics.py` both strip "." and ",", so "12" matches "1.2" [S7] | Specify a decimal- and thousands-safe normaliser plus a T1 test (ext review §7 row 11) |
| M3-E8 | 06 §8.3 item 3 / Ch22 p.10/19 claim "15 or more percentage points" | Unsourced in the book. The nearest verified evidence is mixed: evidence-before-score raised GPT-4's κ from 0.24 to 0.30–0.33 [S4], and chain-of-thought cut math-grading failures from 70% to 30% [S3] | Keep "the magnitude is not verified" (06 already says so) and cite [S3]/[S4] as the evidence |
| M3-E9 | `.claude/skills/llm-as-judge` 7-step loop | Runs the judge on dev while iterating. Under D-10 that loop may only run inside the end-of-course window (ext review §7 row 15b) | Lesson note: build and freeze the prompt now, run it then |
| M3-E10 | `.claude/skills/collaborative-annotation` κ code | Divides by (1 − p_exp) with no guard. It crashes, or returns a misleading value, when both raters use one label (same slip as AE Ch4's kappa function) | Use `contracts_check.cohens_kappa` (returns None) |

### 5. What the research says

- **Claim-level faithfulness is the standard, and it is precision-only.**
  - *Study:* RAGAS split answers into statements and checked each against the context, on 50 WikiEval pages with pairwise human judgments [S1].
  - *Result:* faithfulness agreed with the human pairwise choice 95% of the time, answer relevance 78%, context relevance 70%.
  - *Limits:* 50 easy pairwise items, not absolute labels.
  - *Supporting evidence:* FActScore (biographies, human-edited atomic facts) reached 88–96% annotator agreement and states it measures precision, not recall [S5].
  - *For your project:* claim-level faithfulness is right, but it cannot see omissions, so completeness stays a separate metric.
- **Citation quality has two halves.**
  - *Study:* ALCE defines citation recall (each statement is entailed by its citations) and citation precision (each citation is needed), with an NLI model, on 3,000 examples [S6].
  - *Result:* human agreement κ was 0.70 for recall and 0.53 for precision. About half of ChatGPT and GPT-4 ELI5 answers were not fully supported.
  - *For your project:* page-hit checks only the *place*; support needs human labels now and a judge or NLI later (V1).
- **EM and F1 follow the official script, which has two traps.**
  - The SQuAD 2.0 evaluate script lower-cases, strips all punctuation, removes a/an/the, collapses whitespace, takes the best match over the gold answers, and scores an empty prediction 1 only when the gold is also empty [S7].
  - *Inference from the verified code:* "1.2" and "12" normalise to the same string, and so do "$1,000" and "1000".
  - *For your project:* use a decimal-safe normaliser, map the fixed abstention string to abstention metrics (not to ""), and keep F1 for short-answer categories only.
- **Judges have measured biases.**
  - *Position:* GPT-4 kept the same verdict 65% of the time when the answers were swapped [S3]; with ChatGPT as the judge, 66 of 80 outcomes flipped [S4].
  - *Verbosity:* a repeated-list attack fooled GPT-3.5 and Claude-v1 91.3% of the time and GPT-4 8.7% [S3].
  - *Self-preference:* rises with self-recognition [S8].
  - *Agreement with humans:* GPT-4 reached 85% with experts on non-tie votes, against 81% human–human [S3].
  - *For your project:* a Cohere judge for a gpt-oss generator lowers the self-preference risk. Pointwise, one-criterion, binary judging with a rationale first reduces position and scale effects.
- **How many labels does a judge need?**
  - ARES needed about 150 human labels at minimum to separate systems, with PPI confidence intervals [S2].
  - AE suggests 30–50 Pass and 30–50 Fail in each of dev and test (AE Ch5, 'Data Splits…').
  - *For your project:* the 30-label pilot drafts the rubric. Certification needs the separate ≥ 30/≥ 30 validation set (06 §8.4), and more if the intervals are too wide.
- **Agreement is not accuracy.**
  - Judging the Judges (400 TriviaQA questions, 13 judges) found that high percent agreement hid 10-point score gaps, that rankings stayed right while absolute scores were wrong, and that most judges were lenient [S9].
  - TREC 2024 automatic nuggets ranked runs well (τ 0.78) but per topic only weakly (τ 0.52) [S12].
  - *For your project:* report the class-wise rates (TPR, TNR) with intervals; κ is a secondary number (M3-E5).
- **Criteria come from reading outputs.** EvalGen's study of 9 practitioners found that grading outputs is how people define the criteria ("criteria drift") [S10]. So write the pilot rubric *after* open-coding the first answers, and re-label the early units.
- **Retrieval and generation can be separated per claim.** RAGChecker's claim metrics (claim recall in the retrieved chunks, context utilisation, noise sensitivity, hallucination, self-knowledge) correlated better with humans than RAGAS (Pearson 61.9 vs 48.3; human–human 70.1) [S11]. This is the blueprint for the end-batch diagnostics.
- **Sampling consistency is the book's other hallucination signal.** SelfCheckGPT samples several answers and flags sentences the samples disagree on (GPT-3 on WikiBio; EMNLP 2023) [S14]. The abstract does not give numbers. It needs repeated generations, so it fits beside M4's flip-rate data; detection belongs to V4.
- **String-matched abstention undercounts.** In RGB, rejection measured by exact match (24.7%) was about half the judged rate (45%) [S22]. The course's fixed abstention string makes detection exact only if the model uses it verbatim, so log near-miss refusals as a C5 flag.
- **Current practice:**
  - binary labels with a written critique;
  - one criterion per judge;
  - the rationale before the label;
  - reference-guided prompts where gold exists (math failures fell from 70% to 15% [S3]);
  - judges validated on TPR/TNR with train/dev/test splits [S13, S20, AE Ch5].
- **Interview questions:**
  - How do you trust your judge? (AIQ 07 Q17)
  - Judge biases and their mitigations (AIQ 07 Q16)
  - Faithfulness measurement (AIQ 07 Q24)
  - Why EM and BLEU fail on LLM output (AIQ 07 Q10)
  - Abstention thresholds (AIQ 04 Q60)

### 6. Lesson blueprint

**The answer first.** Retrieval metrics say whether the evidence arrived; generation metrics say what the model did with it. They split into checks that code can do exactly (exact match, token F1 for short answers, the abstention string, whether a citation points at a gold page) and judgements that need a reader (are the claims supported by the context, is the answer correct and complete, does each citation support its sentence). Until the end of the course, you are that reader: about 30 labelled answers from v0, with one labelling unit per metric, which is a pilot for writing the rubric, not proof that any judge works. An LLM judge is a cheaper reader with known biases (position, length, its own family), so the course builds it now but runs it once at the end, and certifies it only if it catches failures *and* keeps good answers often enough, measured against your labels. Correct is not the same as faithful: on a public climate PDF the model may answer from memory, so a closed-book control is needed to tell retrieval working from the model already knowing.

**The theory in one read (12 ideas).**
1. *The triad:* query–context (context relevance), context–answer (faithfulness), query–answer (answer relevance) (Ch22 p.2–4/19).
2. *Correct vs faithful:* correctness against gold; faithfulness against the retrieved context; the 2×2.
3. *Deterministic answer checks:* EM = 1[norm(pred) = norm(gold or alias)]; F1 = 2PR/(P + R) over token multisets; a decimal-safe norm.
4. *Abstention:* positive = should abstain. P = abstained∧unanswerable / abstained; R = abstained∧unanswerable / unanswerable; false-abstention rate = abstained∧answerable / answerable.
5. *Citations:* page-hit = 1[cited pages ∩ gold pages ≠ ∅]; citation precision = supporting citations / citations; citation recall = sentences with a supporting citation / factual sentences.
6. *Faithfulness:* supported claims / claims (Ch22 p.8/19). Completeness = reference claims present / reference claims.
7. *Reference-based vs reference-free:* which metrics need the gold.
8. *Judges:* why they work (a narrower task), the four practices, the three biases, and the evidence numbers.
9. *Structured output:* schema → validate → one retry → log the failure; a valid schema is not a correct label.
10. *Labelling:* units per metric; pilot ≠ certification; the rubric is written after reading (criteria drift).
11. *Measuring a labeller or a judge:* κ = (p_o − p_e)/(1 − p_e); TPR, TNR; Wilson interval (p̂ + z²/2n ± z√(p̂(1−p̂)/n + z²/4n²))/(1 + z²/n).
12. *Controls:* closed-book (floor), oracle context (ceiling), context swap (ignoring retrieval); θ̂ = (p_obs + TNR − 1)/(TPR + TNR − 1) for the end batch (Full).

**Formula sheet:** EM, F1, abstention P/R/F1, false-abstention rate, page-hit, citation P/R, faithfulness, completeness, κ, TPR/TNR, Wilson, θ̂.

**Step-by-step outline (running example: v0 answers for the Corpus D seeds D-001…D-010; recorded once, then replayed).**
1. Read D-002's v0 answer. Compute EM and F1 against "2015" (EM 0, F1 0.333). Add lenient containment.
2. D-001: show the decimal trap with the official normaliser, then fix it.
3. D-009 and D-010 (unanswerable): did v0 abstain with the exact string? Fill the abstention table.
4. D-005: split the answer into claims. Label each against the retrieved context: supported / unsupported / contradicted.
5. D-003: show "faithful to the p.6 distractor, wrong against gold".
6. D-007: check the citations. Page-hit on p.29 only, then "does p.29 alone support the multi-hop answer?"
7. Closed-book control: the same 10 questions with no context. Which were already right?
8. Label 30 answers with the helper (keys c / p / w / d). Write the rubric's "partial" and "wrong" definitions from your notes.
9. Re-label 10 of them 7 or more days later. Compute agreement and κ (or "not estimable"), with Wilson intervals.
10. Read the frozen judge prompt `judge_faithfulness_v1`. Do not run it (D-10). Estimate its end-batch cost.

**Visuals:**
- **Triad triangle** (SVG), with the metric on each edge and the stage it isolates.
- **2×2 correctness × faithfulness grid** with the seed items placed in it. Shows parametric and distractor answers.
- **Claim ladder for one answer:** sentence → claims → label → score.
- **"Agreement is not accuracy" bar pair:** the always-"supported" checker at 0.90 agreement with κ = 0 and failure-catch 0/10.
- **Wilson interval vs n** chart. Shows why 10 labels prove little.

**Full only:**
- BLEU, ROUGE and BERTScore;
- SelfCheckGPT;
- ALCE's NLI definitions;
- RAGChecker's claim metrics;
- the TREC nugget method;
- position-bias numbers and the swap protocol;
- θ̂ with its bootstrap and the judgy caveat;
- the cluster bootstrap for claims within an answer;
- the certification rule (M3-E5).

### 7. Verify notebook plan

`study/notebooks/M3_generation_metrics_verify.ipynb`.
1. Rebuild the 06 §7.4 toys (F1 0.333, faithfulness 0.75, citation P 0.75 and R 0.667, abstention P 0.636 / R 0.700 / F1 0.667, false-abstention 0.08). Assert them.
2. Re-implement the official SQuAD v2 normaliser exactly. Show "12" vs "1.2" giving EM 1, then the decimal-safe version giving 0. Include the AIQ test cases: "cat cat cat" vs "cat" = 0.5; both empty = 1.
3. Wilson for 8/10 (0.490–0.943), against the Wald interval going above 1. κ toys: the always-"supported" checker (κ = 0); the always-disagree raters (κ = −1); one label only (None).
4. The ext review's re-label trap: about 10 items with one unanswerable label moved, giving agreement 0.80 and κ = −0.11.
5. **Optional, cached:** generate v0 answers for the 10 seeds (10 Groq calls) plus closed-book answers (10 Groq calls). Run in `record` mode once; afterwards `replay` only. Compute EM/F1, abstention and page-hit. Show the 2×2 with the closed-book column.

API calls: 0 by default, 20 Groq calls optional (cached). Runtime under 1 minute replayed.

### 8. Apply-it tool plan and real-world checklist

`study/tools/answer_eval.py`: "How good are my system's answers, by code, and what do I need to label by hand?"
- **Inputs:** `--evalset` (M1 format, or `{q, gold, aliases, answerable}`); `--answers` (JSONL `{qid, answer, citations, finish_reason, context_ids}`, or a v0 `results.jsonl`); optional `--labels` and `--labels2` (two human passes); `--abstain-string`.
- **Output:**
  - deterministic metrics per category with n;
  - flags (length stop, empty answer, near-miss refusal, cited page not retrieved);
  - a **labelling sheet** (CSV or JSONL) with the right unit per metric;
  - agreement report with κ and Wilson intervals;
  - the checklist and a recommendation.

**Real-world checklist (12 checks)**

| # | Check | Auto / manual |
|---|---|---|
| C1 | EM/F1 only on short-answer categories, with a decimal-safe normaliser and aliases | auto |
| C2 | The abstention string is detected exactly; near-miss refusals are listed | auto + manual (read the list) |
| C3 | Faithfulness and citation metrics exclude abstentions (n printed) | auto |
| C4 | No cut-off answers: `finish_reason` ≠ "stop" and empty answers are flagged and counted | auto |
| C5 | Cited pages exist in the retrieved context (no citation to an unretrieved page) | auto |
| C6 | Closed-book control run: answers already correct with no context are flagged | auto (when supplied) |
| C7 | Human labels use the right unit per metric (claim / citation / answer) | auto (schema) + manual |
| C8 | The rubric was written after reading answers; early labels were re-labelled under the final rubric version | manual: compare `rubric_version` across labels |
| C9 | Self-agreement on 10 re-labelled answers reported with n; κ only when estimable | auto |
| C10 | The ~10 answers read per version include 5 fixed-seed random dev items | auto (the tool draws them) |
| C11 | No judge score is used for a decision before the end batch | manual |
| C12 | Answer length vs label is checked (a length-bias warning, for when the judge runs) | auto |

**Recommendation logic:**
- C4 fails → "fix `max_completion_tokens` / `reasoning_effort` first (C5 D.6)".
- C6 shows many closed-book-correct items → "Corpus D cannot show retrieval effects for these; weight Corpus T".
- C9 κ is low → "the rubric is unclear; fix it before labelling more".
- Many faithful-but-wrong answers → "retrieval or distractor problem (M5)".
- Many correct-but-unfaithful answers → "parametric answering; check the prompt (P7) and V-phase grounding".

### 9. LLMOps notebook plan

`study/llmops/notebooks/M3_answer_eval_ops.ipynb`: answer evaluation in production style, with the judge path built but not run.
- **Framework build:**
  - The v0 generation step as an LCEL chain over `CachedChatModel` (prompt `answer_v1`); maps to the generate step.
  - Evaluators: EM/F1, abstention, page-hit, citation format and length flags as code evaluators.
  - A **`CohereJudgeEvaluator`** whose call path is complete but whose provider in Phase 3 is a `FakeJudge` that returns schema-valid fixed verdicts. The real Cohere call happens only in the end batch (D-10). Maps to the judge step.
  - **Defaults to name:** `ChatGroq`'s `temperature=0.7` and `reasoning_effort=None` → server `medium` (foundation §9.2) are why the adapter sets every parameter. LangChain structured output can silently retry; the course logs every retry.
- **External calls (cached):**
  - v0 generation over the frozen set: about 55 Groq calls, normally reused from C6's traces (0 new).
  - Closed-book control: about 55 Groq calls.
  - Oracle-context control: about 55, if decision 1 says yes.
  - Context-swap probe on 20 dev items: 20.
  - Total new ≈ 75–130 Groq calls ≈ 130 × (~1,200 input + ≤ 512 output) ≈ **$0.03** (Groq gpt-oss-20b, $0.075/$0.30 per 1M).
  - At 8K TPM (plan **UNVERIFIED**) that is at least about 25 minutes, resumable.
  - Claude Sonnet 5.5 as a *comparison generator arm* only (06 §9.2): about 55 calls ≈ $0.45. Not needed for Phase 3.
- **Tracing:**
  - Every answer has an LLM span (model requested and returned, `system_fingerprint`, all parameters, tokens incl. reasoning, `finish_reason`, latency, cost, `cache_key`) and evaluator spans with scores.
  - Human labels are attached as annotations: local JSONL (`labels.jsonl` with `labeller`, `rubric_version`, `unit`); Phoenix annotations for the local view; LangSmith feedback for Corpus D only.
- **Dataset and evaluators:** the frozen D set; deterministic evaluators every run; human labels as the reference; **no LLM judge until the end batch**.
- **Experiment:** v0 against the closed-book control and the oracle control on identical comparison keys. This gives the floor / actual / ceiling of answer quality, and it is the first experiment in the registry (E001).
- **Cost and latency:** p50/p95 of the LLM span (Groq `queue_time` reported separately); tokens per answer, with the reasoning share; cost if called vs cost paid (replay = $0).
- **Prompt and config versioning:**
  - `prompts/answer_v1.txt`, `prompts/judge_faithfulness_v1.txt`, `judge_correctness_v1.txt`, `judge_citation_v1.txt`: frozen files with sha256 values in the trace.
  - The judge prompt version is part of the end-batch cache key (foundation §2.8).
- **Monitoring and feedback:**
  - Monitor: length-stop rate, empty-answer rate, abstention F1 per version, closed-book-correct share, and label counts per class (are there ≥ 30 failure units yet?).
  - Alert when the length-stop rate is above 5%, or when a new `system_fingerprint` appears.
  - Disagreements between human labels and the deterministic checks feed M5.
- **Lifecycle:** Measure (code checks plus human labels). The end batch is Measure for judges (`llm-as-judge`, `judge-validation`). dev → CI: T2 abstention, page-hit and EM/F1 regression.
- **End-batch preview (plan only):**
  - About 165 judge calls per judged version (06 §8.6): 3 or 4 versions plus a variance run is about 700–1,000 Cohere calls, at or near the trial cap of 1,000 per month (foundation decision 5).
  - judgy for θ̂, with the M3-E6 fix.
  - **Cohere format constraint:** `response_format` (JSON with a schema) cannot be combined with the `documents` parameter, so the judge prompt must carry the numbered contexts inside the message text (verified [S48]). Whether temperature 0 is accepted is UNVERIFIED; record the value actually sent (ext review §7 row 16).
- **Skills:** `code-based-evaluators`, `llm-as-judge`, `judge-validation`, `collaborative-annotation`, `human-review-interfaces`, `rag-evaluation`, `llm-observability`.

### 10. Tools, frameworks, libraries and LLMs

The shared rows are in M1 §10. M3's own rows:

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| EM / F1 | our own decimal-safe normaliser, modelled on the SQuAD v2 script [S7] | — | — | yes | — | — | yes |
| Wilson and exact intervals | `scipy.stats.binomtest(k, n).proportion_ci(method="wilson")` | 1.18.1 | yes | yes | — | BSD-3 | yes |
| κ (cross-check) | `sklearn.metrics.cohen_kappa_score(..., replace_undefined_by=nan)`; the course's own `cohens_kappa` returns None when κ is undefined | 1.9.1 | yes | yes | — | BSD-3 | yes |
| Judge-output schema | `jsonschema` / `pydantic` (dates as `dt.date`, not AE's form) | 4.26.0 / 2.13.5 | yes | yes | — | MIT | yes |
| Generation for the controls | Groq gpt-oss-20b via `CachedChatModel` | — | — | replay yes | about 75–130 new calls ≈ $0.03 | — | yes |
| Corrected success rate (end batch) | `judgy.estimate_success_rate` (holds p_obs fixed; add the M3-E6 resampling) | 0.1.0 | no | yes | — | MIT | yes, end batch only |
| Labelling helper | stdlib page inside `study/app/server.py` (keys c / p / w / d; blind mode; JSONL output) | — | — | yes | $0 | ours | yes (decision 5) |
| Fallback labelling UI | `ipywidgets` | 8.1.9 | no | yes | — | BSD-3 | yes (19 packages) |
| Not used | `label-studio` 1.23.2 (158 packages, Django, `COLLECT_ANALYTICS` default on, Sentry DSN); `argilla` 2.8.0 (server + Elasticsearch; pins pydantic~=2.9) | — | no | server | — | Apache-2.0 | **no** |
| Read only | `ragas` 0.4.3: faithfulness, answer relevancy, the non-LLM `NonLLMStringSimilarity` and `ExactMatch` metrics | — | no | — | — | Apache-2.0 | definitions only |
| Avoid | `deepeval` 4.2.8: telemetry opt-out `DEEPEVAL_TELEMETRY_OPT_OUT=1`; it **loads `.env` from the working directory** (disable with `DEEPEVAL_DISABLE_DOTENV=1`); writes `.deepeval/` (key store, test-run caches); falls back to an OpenAI model | — | no | — | — | Apache-2.0 | **no** |
| Read only | `arize-phoenix-evals` 3.9.0: `@create_evaluator(kind="code")` wraps a plain function | — | no | yes | — | **Elastic-2.0** | definitions only |

**Install lines** (do not run): none for the M3 core. End batch only: `uv add --group eval judgy==0.1.0`.
**Keys:** none until the end batch (`COHERE_API_KEY`, production key; foundation decision 5). Codex labels are not an API call.

### 11. Open questions for Yash (preferences only)

- When the labelling helper shows an answer, should it hide the retrieved context until you have judged correctness (it then needs two passes), or show everything at once? **two-pass / one-pass** (two-pass keeps correctness from leaning on the context; it is slower).

---

## Concept M4: Experimental discipline

### 1. Sources checked

- **Book (verified):**
  - Ch22 p.13–14/19: component-level vs end-to-end; use both.
  - Ch22 p.14–15/19: latency percentiles (p50, p95, p99), time to first token, per-component time, tokens and cost per query, the k trade-off.
  - Ch22 p.15/19: A/B tests isolate one variable and need enough queries; the production loop.
  - Ch22 p.11–12/19: the noise-ratio sweep.
  - App p.12/23: measure before and after every change.
- **Repo (verified):**
  - `choose_chunk_size.ipynb` cells 6–12: the canonical anti-example (§4).
  - `all_rag_techniques_runnable_scripts/simple_rag.py` L36–L57: wall-clock timing only, and `run()` returns None.
  - `helper_functions.py` L294–L321: the retry helper re-awaits a coroutine.
- **Course files:**
  - 02 M4 card; 03 M4 edges and Gate 9→10; 04 M4 row.
  - 06 §4.1 rules, §7.5 percentiles, §9.1–§9.6 (registry, controls checklist, paired group bootstrap, the ~50-question power toy, ablation, T1/T2 tests).
  - `LLMOPS_FOUNDATION.md` §2 (cache and replay), §2.7 (determinism), §8 (local CI).
  - `contracts_check.py` functions `ref_paired_bootstrap`, `make_comparison_meta`, `comparison_keys_match`, `binom_cdf`.
- **AE book:**
  - AE Ch9, 'CI: Building a Safety Net Against Regressions', 'Common Mistakes with CI', 'Revisiting Prompts When Models Improve', 'Judge Drift'.
  - AE Ch5, 'Data Splits for Designing and Validating LLM-as-Judge'.
  - AE has no paired test, McNemar, pre-registration or equal-budget rule, so those parts rest on primary statistics sources.
- **Interview repo:**
  - AIQ 07 Q11, Q25, Q26, Q31, Q32, Q41, Q45, Q47, Q51.
  - AIQ 08 Q11 (as secondary).
- **External:** [S27] Dror et al. · [S30] Bowyer et al. · [S31] number checks · [S32] Koehn · [S33] Berg-Kirkpatrick et al. · [S34] Card et al. · [S35] Miller · [S36] Brown, Cai & DasGupta · [S37] SciPy/statsmodels/NumPy docs · [S38] Dwork et al. / Recht et al. · [S39] Sclar et al. · [S40] Atil et al. · [S41] Thinking Machines · [S15] The Power of Noise.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | One changed variable; controls held fixed; config diff | 06 §4.1 rule 2, §9.2 | 06 only | M4 | no | core | `choose_chunk_size` critique: list every uncontrolled variable |
| 2 | Comparison keys; aligning by qid; refusing different qid sets | 06 §6.6, §9.3 | 06 only | M4 (M1 defines the keys) | no | core | Show a refused comparison |
| 3 | Paired comparison: why pairing removes between-question variance | 06 §9.3 | **missing** | M4 | no | core | Variance formula with the −2Cov term [S35]; worked toy |
| 4 | Bootstrap: resample, recompute, percentile interval | 06 §9.3 | **missing** | M4 | no | core | Hand demo with 5 items, then code |
| 5 | Cluster bootstrap by `group` | 06 §9.3 | **missing** | M4 | no | core | Paraphrase variants counted twice would shrink the interval; Miller's clustered SE ratios (1.1–3×) [S35] |
| 6 | Discordant pairs; exact sign test / McNemar | 06 §9.3 | **missing** | M4 | no | core | "+10 / −6 → p = 0.45" (checked [S31]); McNemar is the binary case of the sign test [S27] |
| 7 | Small-n caution: normal-approximation and percentile-bootstrap intervals undercover below a few hundred items | 06 §9.3–9.4 | **missing** | M4 | no | core | Lead with the exact test for binary metrics; label the bootstrap interval as approximate [S27, S30] |
| 8 | Power and minimum detectable effect; ~50 items detect ~18 points | 06 §9.4 | 06 toy only | M4 | no | core | The checked derivation (SE 0.063, ±0.124, MDE 0.177) [S31]; Card et al.'s power results [S34] |
| 9 | Type-M / Type-S errors (underpowered wins exaggerate) | — | **missing** | M4 | no | core (Full) | One paragraph [S34] |
| 10 | Multiple comparisons; selecting on dev, one test touch, holdout | 06 §9.4 item 3 | 06 only | M4 | no | core | 1 − 0.95¹² = 0.46 (checked); Holm as an option; the reusable-holdout idea [S38] |
| 11 | Pre-registration and the "supported / not supported / inconclusive" verdict | 06 §4.1 rule 4; per-technique gate | 06 only | M4 | no | core | Template filled for a toy experiment |
| 12 | Equal-k vs equal-token-budget comparisons; ablation | 06 §9.2, §9.5 | 07 Part I (written, not studied) | M4 (I1 uses it) | no | core | Two arms with different chunk sizes: compare at k and at equal tokens |
| 13 | Temperature 0, seeds, nondeterminism; replay as the repeatability guarantee | 06 §3.1; foundation §2.7 | P1 (exposed) | P1 / M4 | exposed (P1) | core | Thinking Machines' result and Atil et al. [S40, S41]; Miller's caution on lowering temperature [S35] |
| 14 | Generator flip rate (record mode, samples 1 and 2) | ext review §4 M4; foundation §2.7 | **missing** | M4 | no | core | 10 dev items × 2 reruns; count changed answers |
| 15 | Caching and replay, keyed by content | 06 §9.2; foundation §2 | foundation only | D2 / foundation | no | bridge | One page: what replay guarantees and what it does not |
| 16 | Library versions and environment record (`uv.lock` hash, `env.json`) | 06 §9.1 | O2 (done) | O2 | exposed | bridge | One line |
| 17 | Regression set vs eval set; T1 test with tolerance; injected regression | 06 §9.6; Gate 9→10 | **missing** | M4 | no | core | AE Ch9: CI is a smoke test, not a quality estimate |
| 18 | Per-qid flip report (a mean tolerance hides cancelling flips) | ext review §4 M4 | **missing** | M4 | no | core | "5 fixed + 5 broken passes a mean check"; gate on worsened count |
| 19 | Embedding canary (silent provider change) | foundation §8.4 | **missing** | M4 | no | core (Full) | 3 fixed strings, cache bypassed, tolerance from two runs |
| 20 | Latency percentiles (method named; p95 with small n is near the maximum) and cost accounting | 06 §7.5; Ch22 p.14/19 | 06 only | M4 (D2 later) | no | core | The 06 toy: nearest-rank vs linear give different p95 |
| 21 | Component vs end-to-end evaluation | Ch22 p.13–14/19 | **missing** | M4 | no | core | Development tool vs acceptance test |
| 22 | Noise-ratio robustness sweep (fixed k, varying relevant share) | **Ch22 p.11–12/19** | **missing, no owner** (04 says "M4/V4 experiment") | M4 → V4 | no | bridge | Describe the design; random noise can *help* while distracting noise hurts [S15]; the book's "collapse past ~50%" claim is unsourced. Run it in V4 or X-phase, not here |
| 23 | Prompt format as a hidden variable | ext review §4 M4 | **missing** | M4 | no | core | Up to 76 points from formatting alone [S39] |
| 24 | Infrastructure errors (429, 5xx, timeout) are rerun, never scored | ext review §7 row 21 | **missing** | M4 | no | core | Rule box; an empty `length` answer *is* a quality failure |

### 3. Quiz coverage

There is no question file. Needed titles:
- **R:** Why compare per question rather than two averages? · What must be identical for two runs to be comparable? · Why touch the test split only once per selection round?
- **A:** 10 questions improved, 6 worsened: the exact sign-test p-value? (★item: 0.45.) · Given per-question CE@4 for v0 and a candidate with paraphrase groups, run the group bootstrap by hand on a 5-group toy. · Nearest-rank vs linear p95 for 10 latencies (06 toy).
- **T:** Critique `choose_chunk_size`: list the uncontrolled variables and write a config that fixes each. · "Regression set vs eval set: name two differences" (★item). · A grid of 36 chunk configurations has a winner on dev: what do you do next?
- **Interview:** AIQ 07 Q41, "Your new prompt scores 78% vs the old prompt's 74% on a 100-example eval. Do you ship it?" Second choice: AIQ 07 Q31 (examples needed for a 3-point improvement).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| M4-E1 | 02 M4 card Book list; 04 Ch22 table row 8 | The noise-robustness sweep (Ch22 p.11–12/19) is mapped to "M4/V4 experiment" in 04, but M4's card does not list it and no card runs it. The book's collapse claim is unsourced, and [S15] found that random documents *improved* accuracy (up to 35%) while distracting ones hurt | Give it an owner (V4 or an X-phase card); teach the design and the mixed evidence in M4 as a bridge |
| M4-E2 | 06 §3.1 "temperature 0 [N] for repeatability"; 02 M4 outcome | Temperature 0 does not make a hosted model repeatable [S40, S41]; Miller advises against lowering temperature to cut variance unless that is the deployed setting [S35]. Repeatability comes from replay (foundation §2.7) | Reword: "temperature 0 is the fixed deployed setting; repeatability comes from cached replay; variance is measured by the flip rate" |
| M4-E3 | 06 §9.3 | The percentile group bootstrap is the only interval named. At n ≈ 50, [S30] warns that normal-approximation intervals understate uncertainty below a few hundred items, and [S27] calls the bootstrap less effective on small test sets | Keep it, label it approximate, and lead with the exact sign/McNemar test and the discordant counts for binary metrics (already required in §9.3's last paragraph) |
| M4-E4 | 06 §9.3 sketch vs SciPy | `scipy.stats.bootstrap(paired=True)` resamples items, not groups, and defaults to BCa [S37] | Keep the hand-written group bootstrap; if SciPy is used for cross-checks, set `method="percentile"` and note the per-item resampling |
| M4-E5 | 06 §9.6 `TOL` on means | A mean tolerance passes when fixes and breaks cancel (5 + 5 = net 0) | Add the per-qid flip list and a cap on worsened items (ext review §4 M4) |
| M4-E6 | 04 M4 row "5 reruns of v0 at temperature 0, with and without a response cache" | With the course cache (foundation §2.5), "without cache" means `record` mode with samples 1…5; a cached rerun proves only replay | Reword to the record-mode sample design |
| M4-E7 | `choose_chunk_size.ipynb` cell 8 (cited as "custom prompt key likely a no-op") | Confirmed as a placeholder key `"your_prompt_key"`. The judge is `gpt-4o`, while the comment says GPT-4. llama-index is not installed, so the no-op behaviour is **UNVERIFIED** | Keep "likely a no-op (UNVERIFIED)" |

### 5. What the research says

- **Paired resampling is the standard, and its origin is in NLP.**
  - *Study:* Koehn (EMNLP 2004) resampled sentences 1,000 times to compare MT systems on BLEU, checked against a 30,000-sentence near-true set [S32].
  - *Result:* the method was slightly conservative (conclusions at 90–95% confidence were right 95% of the time). Blocks of consecutive sentences varied far more than broad samples (21–37% vs 27–31% BLEU).
  - *What it means:* paired resampling works, and correlated items inflate apparent certainty.
  - *For your project:* resample whole groups (paraphrases), as 06 §9.3 does.
- **Small test sets need large gains.**
  - *Study:* Berg-Kirkpatrick et al. (EMNLP 2012) measured significance thresholds across five tasks and test sizes [S33].
  - *Result:* on parsing, the gain needed for p < 0.05 fell from 3.00 F1 at 100 sentences to 0.22 for the full corpus. Near-threshold wins kept their sign on another domain only 48% of the time.
  - *Further evidence:* Card et al. (EMNLP 2020) showed that many published comparisons were underpowered, and that underpowered significant wins exaggerate the effect [S34].
  - *For your project:* at ~50 items expect to detect only gains of ~18 points (06 §9.4, derivation checked [S31]). Plan "inconclusive" as a normal verdict. Run the power check *before* the experiment, from dev agreement.
- **Which test, and its small-sample limits.**
  - Dror et al. (ACL 2018) give a decision tree: exact tests (sign, McNemar) for binary outcomes; bootstrap or permutation when the statistic's distribution is unknown. They note the bootstrap is weak on small test sets, and that only 3 of 110 multi-dataset papers corrected for multiple comparisons [S27].
  - Bowyer et al. (ICML 2025) argue that intervals based on the central limit theorem understate uncertainty in LLM evals with fewer than a few hundred items [S30].
  - *For your project:* report the discordant counts and the exact test first; the group bootstrap interval second, labelled approximate.
- **Error bars for LLM evals.**
  - Miller (Anthropic, 2024) recommends standard errors, clustered SEs for grouped questions (1.1–3.05× wider in his examples), paired differences, and power analysis [S35]. He also advises against lowering temperature just to reduce variance.
  - *For your project:* the flip-rate runs are his "resample answers K times" idea; analyse them by question cluster.
- **Nondeterminism is measured, not assumed.**
  - Atil et al. (2024) found up to 15% accuracy variation across runs configured to be deterministic [S40].
  - Thinking Machines (2025) traced temperature-0 differences to batch-size-dependent arithmetic: 80 distinct completions out of 1,000 [S41].
  - *For your project:* the generator flip rate sets the T2 tolerance, and replay makes notebooks repeatable without pretending the model is.
- **Hidden variables.** Meaning-preserving prompt-format changes moved accuracy by up to 76 points [S39]. Seeds and data order matter too (Bouthillier et al., MLSys 2021). Freeze the prompt file and change one thing at a time.
- **Test reuse.** Adaptive reuse of a holdout overfits it (Dwork et al. 2015, via the Google Research summary) [S38]. Recht et al. found that drops on fresh test sets came from harder items, not adaptive overfitting [S38]. Logging every test touch is the cheap guard either way.
- **Noise robustness (book Ch22 p.11–12/19).** Cuconasu et al. (2024) found that distracting high-scoring irrelevant passages hurt answers, while random passages improved accuracy by up to 35% [S15]. The book's single "collapse past ~50% noise" curve is therefore an oversimplification (an inference).
- **Current practice:** paired, clustered, power-planned comparisons (Miller [S35]); exact or Bayesian intervals at small n (Bowyer [S30]); CI as a regression smoke test, with pinned models (AE Ch9).
- **Interview questions:**
  - 78% vs 74% on 100 examples: ship? (AIQ 07 Q41)
  - How many examples to detect 3 points? (AIQ 07 Q31)
  - Nondeterministic evals: how do you get trustworthy numbers? (AIQ 07 Q45)
  - Aggregate +3 but one segment −8 (AIQ 07 Q47)
  - Wiring evals into CI (AIQ 07 Q25)

### 6. Lesson blueprint

**The answer first.** An experiment is only evidence if exactly one thing changed and everything else (questions, text snapshot, scorer, k or token budget, model and its settings, prompt, library versions) is provably the same, which is why every run records its comparison keys and config and refuses to compare runs that differ. Because both versions answer the same questions, you compare them question by question: count how many got better and how many got worse, and test whether that imbalance could be chance. With about 50 questions only large effects are detectable, so "inconclusive" is a normal, honest verdict, and the decision rule is written down before the run. Selection happens on dev, the chosen version is confirmed once on test, and holdout waits for the capstone; a frozen regression test then stops a later change from silently breaking what already works. The LLM is not repeatable even at temperature 0, so notebooks replay cached responses, and the variation itself is measured with a flip rate.

**The theory in one read (12 ideas).**
1. *One variable:* the config diff has exactly one line; otherwise add a second comparison holding the other variable fixed (equal tokens).
2. *Comparison keys:* (`dataset_sha256`, `snapshot_id`, qid set, labels, split, `scorer_version`).
3. *Pairing:* Var(Ā − B̄) = [Var(A) + Var(B) − 2Cov(A, B)]/n.
4. *Discordant pairs:* b = improved, c = worsened; exact sign test p = 2·P(X ≤ min(b, c) | n = b + c, ½).
5. *Bootstrap:* resample groups with replacement; recompute the mean difference; take percentiles 2.5 and 97.5 (approximate at small n).
6. *Power:* SE ≈ √(b + c)/n; MDE ≈ 2.8·SE at 80% power and α = 0.05.
7. *Multiple comparisons:* P(at least one false alarm) = 1 − (1 − α)^m; Holm as the fix; dev → one test touch → holdout.
8. *Pre-registration and verdicts:* hypothesis, primary and guard metrics, decision rule → supported / not supported / inconclusive.
9. *Nondeterminism:* temperature 0 is a setting, not a guarantee; replay is the repeatability guarantee; flip rate = changed answers / reruns.
10. *Regression tests:* a regression set (known failures) ≠ the eval set (estimate). T1 with tolerance plus a per-qid flip list; an injected regression must fail.
11. *Ops metrics:* p50/p95 with the method named; cost = input × price_in + output × price_out.
12. *Component vs end-to-end:* the component metric tells you where to look; end-to-end tells you whether it matters (Ch22 p.13–14/19).

**Formula sheet:** paired variance; sign-test p; the bootstrap recipe; SE/MDE; the false-alarm rate; Holm's rule; Wilson (from M3); percentile methods; cost per query.

**Step-by-step outline (running example: two real retrieval arms on Corpus D, fully offline, MiniLM top-4 at chunk size 1000/200 vs 500/100, scored with M2's CE@4 on the frozen set, plus a synthetic 50-question toy for the statistics).**
1. Critique `choose_chunk_size` cells 6–12: no baseline, an unseeded sample, an LLM-judged ceiling, stale output, a no-op prompt key.
2. Write the pre-registration for "500/100 beats 1000/200 on multi-span CE@4".
3. Run both arms. Refuse a comparison with a mismatched qid set (show the error).
4. Compute b and c, the exact sign test and the group bootstrap interval. Read the verdict ("inconclusive" is expected at this n).
5. The equal-budget arm: give 500/100 the same context tokens (k = 8) and compare again.
6. Power: from the dev discordance, compute the MDE, and what n would detect 10 points.
7. Flip-rate lab: 10 dev items × 2 `record`-mode reruns (20 Groq calls, cached afterwards). Count changed answers, and log `system_fingerprint`.
8. Write the T1 regression test. Inject a regression (`normalize: false`) and watch it fail; show that cancelling flips pass a mean check.
9. Latency: p50/p95 by nearest-rank and by linear interpolation.

**Visuals:**
- **Paired-difference dot plot:** each question's change, coloured improved / worsened / same. Shows the discordant pairs.
- **Bootstrap histogram** with the interval and 0 marked.
- **Power curve:** MDE against n for discordance rates 10–30%. Shows why ~50 detects only large effects.
- **Flip-rate bar** per item.
- **Equal-k vs equal-budget panel:** the same arms, two framings.

**Full only:**
- Type-M/S errors;
- Holm;
- the reusable-holdout idea;
- Bowyer's small-n critique;
- BCa vs percentile;
- McNemar vs sign test;
- the embedding canary;
- the noise-ratio sweep design and its mixed evidence;
- prompt-format sensitivity;
- infrastructure-error rules;
- the ablation template.

### 7. Verify notebook plan

`study/notebooks/M4_experiments_verify.ipynb`.
1. Number checks (a)–(e), with stdlib and NumPy, asserting the values in §5: SE 0.0632; ±0.124; MDE 0.177; sign p 0.4545; Wilson 0.490–0.943; Clopper–Pearson lower bound 0.541 (two-sided) and 0.607 (one-sided); 1 − 0.95¹² = 0.4596.
2. Group bootstrap: assert that `contracts_check.ref_paired_bootstrap` rejects a missing qid, ignores qid order, and moves a paraphrase with its base. Cross-check the exact sign test and Wilson against SciPy/statsmodels.
3. Coverage simulation: draw 2,000 synthetic 50-item paired experiments with a known difference, and count how often the percentile group bootstrap and the exact sign test cover or reject. This shows the small-n undercoverage that [S30] predicts, on our n.
4. The two real offline retrieval arms on the frozen seed set (MiniLM, CE@4). Report b, c, p and the interval, with an expected "inconclusive".
5. Equal-budget variant (k chosen so that mean context tokens match).
6. Percentile toy (06 §7.5): nearest-rank 900 vs linear 697.5.
7. **Optional, cached:** flip rate on 10 dev items × 2 samples (20 Groq calls in `record` mode; replayed later).

API calls: 0 by default, 20 optional. Runtime about 1–2 minutes (the simulation dominates).

### 8. Apply-it tool plan and real-world checklist

`study/tools/compare_runs.py`: "Did my change really help, or is it noise?"
- **Inputs:** `--baseline results.jsonl --candidate results.jsonl`; `--metric ce@4` (or any per-question field); `--groups` from the eval set; `--prereg summary.md` (reads the decision rule); `--tokens-field` for the equal-budget check.
- **Output:**
  - the key check;
  - aligned per-question table;
  - b and c with the exact test;
  - group bootstrap interval;
  - MDE at this n;
  - per-category deltas with n;
  - flips by qid;
  - the verdict from the pre-registered rule;
  - the checklist.

**Real-world checklist (12 checks)**

| # | Check | Auto / manual |
|---|---|---|
| C1 | Comparison keys identical (dataset hash, snapshot, qid set, labels, split, scorer) | auto |
| C2 | Exactly one config line differs | auto (config diff) |
| C3 | Equal k **and**, where chunk or context size changed, equal token budget | auto (tokens per arm) |
| C4 | Pre-registered hypothesis and decision rule exist and predate the run (commit time) | auto (file + git log) + manual |
| C5 | Selection on dev; test touched at most once this round (`TEST_LOG.md`) | auto |
| C6 | Discordant counts and the exact test reported | auto |
| C7 | Group bootstrap interval reported, labelled approximate at n < ~200 | auto |
| C8 | The MDE at this n is shown; "inconclusive" is used when the interval spans 0 | auto |
| C9 | Guard metrics did not regress beyond tolerance; per-qid flips are listed | auto |
| C10 | Generator settings identical (model id requested and returned, `reasoning_effort`, max tokens, prompt sha) | auto |
| C11 | Infrastructure errors were rerun, not scored | auto (error classes) |
| C12 | Number of configurations tried is logged (multiple-comparison context) | auto + manual |

**Recommendation logic:**
- C1, C2 or C10 fails → "not comparable".
- C4 or C5 fails → "exploratory only".
- Exact test p ≥ 0.05 and the interval spans 0 → "inconclusive: grow the set or accept the champion".
- Supported, and C9 passes → "adopt; rerun v0 alongside".

### 9. LLMOps notebook plan

`study/llmops/notebooks/M4_experiments_ops.ipynb`: experiments, CI and drift as a team runs them.
- **Framework build:** two `langsmith.evaluate(..., upload_results=False)` experiments on the same dataset (v0 vs a candidate config), compared in the course runner. LangSmith's comparison view is used only for Corpus D mirrors. Maps to the run-and-compare steps.
  - **Defaults to name:** `num_repetitions=1`, `max_concurrency=0` and `error_handling="log"` (foundation §4). An error logged as a result would be *scored* unless the runner reruns infrastructure errors (C11).
- **External calls (cached):**
  - Flip-rate lab: 10 items × 2 samples = 20 Groq calls, in `record` mode with samples 1 and 2.
  - Embedding canary: 3 Cohere embed calls per check.
  - Everything else replays.
  - Cost ≈ $0.005.
- **Tracing:** the run root carries `config_hash`, `dataset_sha256`, `snapshot_id`, `cache_mode`, the git commit and `TEST_LOG` touches. Every LLM span shows the `sample` index.
- **Dataset and evaluators:** the M1 frozen set; the M2/M3 deterministic evaluators; the statistics computed offline.
- **Experiment against the previous version:** v0 vs v0 rerun (determinism) and v0 vs the offline chunking arm (the lesson's example).
- **Cost and latency tracking:** cost if called vs paid; p50/p95 per stage; reasoning-token share; rate-limit planning (foundation §2.5).
- **Prompt and config versioning:** `experiments/E0xx/config.yaml`, `env.json` and `summary.md` (pre-registration). Every change enters through a pre-registered run (foundation §7).
- **CI and monitoring:**
  - **pre-commit** runs T1 (metric toys, sufficiency, determinism, cache keys, leakage);
  - **nox** sessions `t1`, `replay`, `t2` (manual), `monitor`;
  - the injected-regression acceptance test;
  - monitor: metric per version, flip rate, `system_fingerprint` changes, canary drift; alert on a canary breach or a new fingerprint.
- **Lifecycle:** Improve, verified by Measure. dev → CI is wired here (Gate 9→10's T1 test is an M4 outcome).
- **Skills:** `ci-cd-evals`, `evals-foundations`, `code-based-evaluators`, `llm-observability`, `improving-llm-agents`.

### 10. Tools, frameworks, libraries and LLMs

The shared rows are in M1 §10. M4's own rows:

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Exact sign / McNemar test | `scipy.stats.binomtest(b, b + c, 0.5)` | 1.18.1 | yes | yes | — | BSD-3 | yes |
| Group bootstrap | our own (06 §9.3; `contracts_check.ref_paired_bootstrap` as the reference). SciPy's `bootstrap(paired=True)` resamples items, not groups, and defaults to `method="BCa"` | — | — | yes | — | — | yes |
| Optional cross-checks | `statsmodels`: `mcnemar(exact=True)`, `multipletests(method="holm")` (its default is Holm–Šidák), `cohens_kappa` | 0.15.0 | no | yes | — | BSD-3 | yes (14 packages) |
| Percentiles | `numpy.percentile(method=...)`: the default is `"linear"`; name the method you use | 2.5.3 | yes | yes | — | BSD-3 | yes |
| Flip-rate runs | Groq gpt-oss-20b in `record` mode, samples 1 and 2 | — | — | replay yes | 20 calls ≈ $0.005 | — | yes |
| Embedding canary | Cohere `embed-v4.0`, cache bypassed (record mode) | — | — | no | 3 texts per check | — | yes |
| Local CI | `pre-commit` (pre-commit and pre-push stages) and `nox` (`uv` backend) | 4.6.2 / 2026.8.17 | no | yes | — | MIT / Apache-2.0 | yes (foundation §8) |

**Install lines** (do not run): `uv add --group dev pre-commit==4.6.2 nox==2026.8.17`; optional `uv add --group dev statsmodels==0.15.0`.
**Keys:** `GROQ_API_KEY` for the 20 flip-rate calls (record once); none afterwards.

### 11. Open questions for Yash (preferences only)

- For the statistics lesson, do you want the coverage simulation (about 2,000 synthetic experiments, showing that small-n intervals undercover), or only the worked examples? **sim / examples**

---

## Concept M5: Failure analysis taxonomy

### 1. Sources checked

- **Book (verified):**
  - App p.3–5/23: six symptom families (wrong documents, missing information, wrong order, wrong or made-up answer, unsupported content type, cannot measure).
  - App p.6–7/23: five layers, with "semantic chunking and reranking first" as an unmeasured claim.
  - App p.12/23: match symptoms to techniques; measure before and after.
  - Ch22 p.1/19: three complaints.
  - Ch22 p.18/19: manual testing as a flashlight.
- **Repo:** none (04 confirms).
- **Course files:**
  - 02 M5 card; 03 §6.3 2×2.
  - 06 §4.1 version table (bucket → card), §7.1.
  - `labs/C6_v0_pipeline.ipynb` cells 43–45: Task 10, the open-coding table with columns qid · would a reader accept it · what went wrong (first problem) · first failing stage · trace evidence, plus a grouping table.
  - C6 §D.5 "Which stage failed? Walk upstream to downstream" (heading only; the body was not read).
  - 08 D-29.
- **AE book:**
  - AE Ch3, 'Open Coding: Reading and Labeling Traces', 'Axial Coding: Structuring Failure Modes', 'Labeling Traces with Structured Failure Modes', 'Iteration and Refinement', 'A Note on Exhaustive Labeling' (sidebar), 'Common Pitfalls'.
  - AE Ch11, 'EDA and Clustering to Surface Hypotheses', 'Beyond Clustering', 'Using AI Coding Assistants'.
  - AE Ch10, 'Selecting Traces for Human Review'.
  - AE Ch1, 'Improve'.
- **Interview repo:**
  - AIQ 07 Q27 (500 failing transcripts) and Q35 (review queue).
  - AIQ 04 Q46 (triage) and Q47 (top failure modes).
  - cohere.md Q5 (10× documents, quality worse).
- **External:** [S19] Barnett et al. · [S42] Errudite · [S25] CheckList · [S43] Saunders et al. (saturation) · [S22] RGB · [S21] CRAG · [S11] RAGChecker · [S29] Husain & Shankar FAQ.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | A trace and its stages (query → candidates → context → prompt → answer → citations) | the input to M5 | C6 (written, not studied; Task 10 not done) | C6 | no | bridge | One annotated v0 trace |
| 2 | The failing stage, walking upstream to downstream | C6 §D.5, lab Task 9 ladder | C6 (not studied) | C6 | no | bridge | Reuse C6's ladder, not a new one |
| 3 | Open coding: the first, most upstream failure, in your own words, no LLM | 02 M5; ext review box | **missing** | M5 | exposed (M5, O1) | core | AE Ch3 method; Errudite's lesson that error groups must be precise [S42] |
| 4 | Axial coding into distinct, countable modes; the split rule (different cards ⇒ different modes) | 02 M5 | **missing** | M5 | no | core | Group the notes by hand; name each with a 02 bucket, a book family or a new name |
| 5 | The 02 bucket list + new buckets (false abstention, output error, omission, ambiguity, label error, unmapped, hub chunk) | 02 M5; ext review §7 row 4 | 02 list only | M5 | no | core | Start from notes, map to buckets afterwards |
| 6 | Barnett's seven failure points as a vocabulary | 02 M5 Ext (marked UNVERIFIED) | **missing** (now verified [S19]) | M5 | no | core | Map FP1–FP7 to our buckets (§5); qualitative, no counts |
| 7 | First-failure vs all-failures counting; the denominator | ext review; AE Ch3 sidebar | **missing** | M5 | no | core | Decision buckets get 0/1 per trace for every failing check; state whether the denominator is all items or failing items |
| 8 | Operational bucket definitions (code-checkable where possible) | Errudite [S42] | **missing** | M5 | no | core | e.g. "rank: CE@pool = 1, CE@4 = 0"; "vocabulary mismatch: gold not in top-k and overlap < 0.3" |
| 9 | Counterfactual confirmation (inject the gold span, swap the context) | Errudite [S42]; M3 controls | **missing** | M5 | no | core | Use M3's oracle and closed-book runs as the counterfactuals |
| 10 | Saturation stop rule; review order logged | ext review box step 5; [S43] | **missing** | M5 | no | core | "Stop when 10 consecutive traces add no new mode and re-coding changes no label"; it is a judgement of degree [S43] |
| 11 | Quick aggregate checks before reading: finish_reason, empty answers, IQR outliers on a log scale, gold rank in the full ranking | ext review box step 2; AE Ch11 | **missing** | M5 | no | core | Clusters and outliers are reading lists, not verdicts (AE Ch11) |
| 12 | Dev and analysis-only traces only; never test or holdout | ext review §7 row 5 | **missing** | M5 | no | core | Bucket counts choose cards, so reading test leaks selection |
| 13 | AI-assistant rule: find, filter, plot only; you fill the bucket column; AI causes go to a hypothesis column | ext review box step 6; AE Ch11 'Using AI Coding Assistants' | **missing** | M5 | no | core | Write the rule into the lesson file itself |
| 14 | Bucket → card mapping and prioritising (count × severity × cost) | 06 §4.1 table; 02 M5 "decide" | 06 only | M5 | no | core | Ranked shortlist; App p.6–7/23's "quick wins" order is a hypothesis to test |
| 15 | The 2×2 (CE@k × answer outcome) and final-context CE | 03 §6.3 | 03 only | M2/M3 | no | bridge | Place every trace in the grid first |
| 16 | Specification vs generalisation (did the prompt ask for it?) | ext review ★item; AE Ch1 | **missing** | M5 | no | core | One column: "Did answer_v1 ask for this behaviour?" |
| 17 | Multi-hop / global bucket (needed by R5 and S1 gates) | ext review §7 row 6 | **missing** | M5 | no | core | Add the bucket, or define the trigger as CE@k on the multi-hop category |
| 18 | Label errors and holes: "retrieval bad, answer good" items reviewed by hand | 06 §7.1 | 06 only | M5 (M1 fixes) | no | core | Route to `ADJUDICATION.md` and the next dataset version |

### 3. Quiz coverage

There is no question file. Needed titles:
- **R:** Why note only the first, most upstream failure in open coding? · What is the difference between open and axial coding? · When do you stop reading traces?
- **A:** Given 6 trace summaries, write an open code for each and group them. · Turn "the answer missed a fact" into a code-checkable bucket definition.
- **T:** "Ch22 calls manual testing a flashlight; AE says read traces first: do they disagree?" (★item). · "A v0 answer picks one meaning of an ambiguous question: prompt gap or ignored rule?" (★item). · An FAQ says most RAG failures are retrieval failures: how would you check that for v0?
- **Interview:** AIQ 07 Q27, "You have 500 production transcripts flagged as failures. Walk me through your error-analysis process." Second choice: AIQ 04 Q47 (top failure modes).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| M5-E1 | 02 M5 Ext; 04 REVIEWER NOTE R-3; 08 D-29 | Barnett et al. 2024 is marked UNVERIFIED. It is now verified: arXiv 2401.05856, CAIN 2024 (IEEE proceedings), 3 case studies, seven failure points, qualitative with no counts [S19] | Register it as Source C and close D-29's RAG-literature part, keeping the "qualitative only" caveat |
| M5-E2 | 02 M5 outcomes (fixed bucket list, counted once) | First-failure-only counts undercount later stages (AE Ch3, 'A Note on Exhaustive Labeling'); a fixed list hides new modes (ext review §7 row 4) | Open-code first; mark every decision bucket 0/1 per trace |
| M5-E3 | 02 R5 and S1 gates | Read a multi-hop/global bucket that is not in the M5 list (ext review §7 row 6) | Add it, or define the trigger as CE@k on the multi-hop category |
| M5-E4 | App p.5/23 (book) | The "cannot measure" family lists adaptive retrieval and feedback loops beside evaluation, which mixes measurement with routing; App p.6–7/23 ranks techniques with no measurement | Teach the symptom map as a list of hypotheses (04 already says so for K1) |
| M5-E5 | `.claude/skills/trace-data-analysis` | Calls the 1.5×IQR rule robust to skew; on skewed metrics it flags much of the upper tail (ext review §8) | Use a log scale; treat flags as a reading list |
| M5-E6 | 06 §4.2 v0.1 "Error-bucket every v0 failure" | No split is named, so it could read test and holdout traces | "dev and analysis-only traces" (ext review §7 row 5; touches M-05, so Codex) |

### 5. What the research says

- **A RAG-specific vocabulary exists, but no counts.**
  - *Study:* Barnett et al. (CAIN 2024) report three RAG case studies (research papers, education content, and BioASQ with 1,000 expert Q&As) [S19].
  - *Result:* seven failure points: FP1 missing content, FP2 missed the top-ranked documents, FP3 not in context (lost in consolidation), FP4 not extracted, FP5 wrong format, FP6 incorrect specificity, FP7 incomplete.
  - *Limits:* qualitative, with no prevalence counts; the raters were not domain experts.
  - *What it means:* the points follow the pipeline order, which supports coding the first, most upstream failure.
  - *For your project:* FP1 → should-have-abstained; FP2 → rank or recall; FP3 → assembly (final-context CE); FP4 → context noise or omission; FP5/FP6 → output or specification; FP7 → incomplete multi-span. Your counts, not the paper, choose the cards.
- **Error analysis must be precise, complete and testable.**
  - *Study:* Errudite (ACL 2019) surveyed 10 papers and ran a 10-person user study [S42].
  - *Result:* published error analyses sampled 50–200 errors, often under 5% of all errors. People given the same error definition produced groups ranging from 13.8% to 45.2% of the errors. Looking only at errors can prioritise groups the model actually handles well.
  - *For your project:* write an operational definition per bucket, compute each bucket's rate over *all* items with that property (not only failures), and confirm causes counterfactually (oracle context, gold injection).
- **Behavioural tests find what accuracy misses.**
  - CheckList (ACL 2020) crosses capabilities with test types: minimum functionality, invariance and directional tests. Users found almost three times as many bugs [S25].
  - *For your project:* paraphrase groups are invariance tests. Report "all variants right" per group, and bucket the inconsistent groups.
- **Retrieval can add hallucination, and abstention needs its own bucket.**
  - CRAG: straightforward RAG raised hallucination to 25–32% [S21].
  - RGB: models rarely rejected when given only noise, at best 45% judged [S22].
  - So *should-have-abstained* and *context noise* deserve separate buckets.
- **Claim-level diagnostics can split retrieval from generation.** RAGChecker's context utilisation and noise-sensitivity metrics [S11] are the automated version of buckets like "omission" and "context noise". They need a judge, so they come at the end batch.
- **When to stop.** Saturation means no new data develop a category further. Saunders et al. caution that it is a prediction and a matter of degree, often in tension with fixed sample sizes [S43]. So record the stop rule and the review order, and mark the taxonomy "provisional" if the rule was not met.
- **Current practice.**
  - Open coding of at least ~30 traces by the domain expert, axial coding into counted categories, and stopping at saturation [S29]; AE Ch3 says at least 20 problem traces.
  - LLMs may help group notes but not write them (AE Ch3; AE Ch11).
- **Pitfalls:**
  - categories chosen before reading;
  - abstract codes ("hallucination");
  - overlapping modes;
  - first-failure undercount;
  - clusters treated as conclusions;
  - asking an AI *why* traces fail (AE Ch11).
- **Interview questions:**
  - 500 failing transcripts: your process? (AIQ 07 Q27)
  - Design a review queue (AIQ 07 Q35)
  - Triage a wrong answer (AIQ 04 Q46)
  - Top failure modes of production RAG (AIQ 04 Q47)
  - 10× documents and quality fell: investigate (cohere.md Q5)

### 6. Lesson blueprint

**The answer first.** Failure analysis turns "it feels wrong sometimes" into a counted list of named problems, and that list, not hype or the book's suggested order, decides which Phase 4–7 techniques are worth trying. You read each failing v0 trace yourself and write one short note about the first, most upstream thing that went wrong; then you group the notes into a few distinct failure modes, give each a definition you could check in code, and count how many traces show each one, with their ids. Simple checks run first (cut-off answers, empty answers, where the gold chunk ranked) so that reading time goes where it is needed, and the "retrieval failed but the answer was right" cases are read for label errors and memorised answers. You stop when new traces stop adding new kinds of failure, read only dev traces so that test stays clean, and let an AI assistant search and plot but never decide the cause. The output is a bucket table and a ranked shortlist of next interventions, each tied to a bucket and to the card in 06 that targets it.

**The theory in one read (10 ideas).**
1. *Trace and stages* (bridge from C6).
2. *The 2×2:* CE@k × answer outcome, then final-context CE for the top-right cell.
3. *Quick checks first:* `finish_reason`, empty answers, gold rank in the full ranking, outliers flagged by a log-scale IQR rule (a reading list only).
4. *Open coding:* one note per trace, on the first, most upstream failure; your words; no LLM.
5. *Axial coding:* group the notes; split groups that would choose different cards; name them (02 buckets, book families, Barnett FPs, or new).
6. *Operational definitions:* each bucket as a check (e.g. rank = CE@pool = 1 ∧ CE@4 = 0).
7. *Counting:* prevalence = traces with the bucket / denominator (state which denominator); for decision buckets mark every bucket a trace shows.
8. *Confirming causes:* counterfactuals (oracle context, closed-book, context swap).
9. *Stopping:* saturation rule; dev and analysis-only traces only.
10. *Choosing:* priority ≈ count × severity, against the cost of the card; the symptom map (App p.3–5/23) as hypotheses.

**Formula sheet:** prevalence; the share of the first failing stage; the saturation rule; the bucket → card table (06 §4.1).

**Step-by-step outline (running example: v0 traces for the Corpus D dev split; until C6 has run, the M2/M3 verify outputs for the 10 seeds serve).**
1. Place every dev trace in the 2×2.
2. Run the quick checks: list length stops, empty answers and gold ranks.
3. Open-code each failing trace in C6's Task 10 table (same columns).
4. Group the notes on paper. Name the groups. Write one operational definition per group.
5. Recount with code using the definitions (0/1 per bucket per trace). Compare with the hand counts.
6. Read the "retrieval bad, answer good" items. Move label errors to `ADJUDICATION.md`.
7. Check saturation. Mark the taxonomy final or provisional.
8. Rank the next interventions and link each to a 06 card and a bucket.

**Visuals:**
- **2×2 scatter** of traces, coloured by bucket.
- **Pareto bar** of bucket counts (with trace ids on hover). Shows where the effort goes.
- **First-failing-stage funnel**: parse → chunk → retrieve → rank → assemble → generate → cite. Shows where failures enter.
- **Saturation curve**: new modes found against traces read. Shows when to stop.
- **Bucket → card map** (a table, not a chart).

**Full only:**
- Barnett's mapping;
- Errudite's precision principles;
- CheckList invariance groups;
- exhaustive labelling;
- the review-sampling mix (random / uncertainty / failure-driven, AE Ch10);
- the hub-chunk sub-tag;
- the multi-hop/global bucket for R5 and S1;
- the specification-gap column;
- saturation caveats.

### 7. Verify notebook plan

`study/notebooks/M5_failure_analysis_verify.ipynb`.
1. Load the M2 offline retrieval run on the 8 answerable seeds, plus (optional, cached) the M3 seed answers and closed-book answers.
2. Compute the quick checks and gold rank in the full ranking (exact search over all chunks).
3. Place the items in the 2×2 and compute final-context CE (same as CE@4 for v0's plain concatenation, which the notebook asserts).
4. Apply example operational definitions for 6 buckets and show the counts with qids (a toy: 10 items give anecdotes, not rates).
5. Saturation curve from a logged review order (a synthetic example, labelled as such).
6. Bucket → card table generated from 06 §4.1.

API calls: 0 (or the M3 cache). Runtime seconds. **No conclusions about v0** are drawn from 10 seeds; the notebook demonstrates the mechanics only.

### 8. Apply-it tool plan and real-world checklist

`study/tools/failure_buckets.py`: "What is going wrong in my system, and what should I fix first?"
- **Inputs:** `--traces results.jsonl` (06 §2.5 trace format or a light form); `--evalset`; optional `--controls closed_book.jsonl oracle.jsonl`; `--codes codes.csv` (your open codes, filled after the first pass).
- **Pass 1:** writes a **coding sheet**, one row per failing dev trace with the auto-computed facts (CE@k, gold rank, final-context CE, finish_reason, abstained, page-hit, closed-book correct) and empty columns for your note, first failing stage and "did the prompt ask for it?".
- **Pass 2:** reads the filled sheet and produces:
  - bucket counts with trace ids;
  - decision buckets recounted 0/1 from the operational definitions;
  - the saturation status;
  - the ranked shortlist mapped to cards.

**Real-world checklist (11 checks)**

| # | Check | Auto / manual |
|---|---|---|
| C1 | Only dev / analysis traces are included; test and holdout are refused | auto |
| C2 | Quick checks ran first (length stops, empty answers, gold rank) | auto |
| C3 | Every failing trace has a human note on the first failure (no blank, no LLM-written note) | auto (completeness) + manual |
| C4 | Notes are concrete ("cited p.6 instead of p.23"), not labels ("hallucination") | manual: reread 5 at random |
| C5 | Each bucket has an operational definition, and the code recount agrees with the hand count | auto |
| C6 | Decision buckets are counted for every occurrence, not first only | auto |
| C7 | The denominator is stated (all items or failing items) | auto |
| C8 | "Retrieval bad, answer good" items were read for label errors and memorised answers (closed-book column) | auto (list) + manual |
| C9 | The saturation rule was met, or the taxonomy is marked provisional | auto (from the logged review order) |
| C10 | AI-proposed causes are in a hypothesis column, never in the bucket column | manual |
| C11 | Each shortlisted intervention names its bucket, its count and its 06 card | auto |

**Recommendation logic:**
- the top bucket by count × severity → its card;
- recall vs rank decided by CE@pool vs CE@k;
- many closed-book-correct items → "weight Corpus T";
- many label errors → "fix the dataset first (M1)";
- saturation not met → "read 10 more before deciding".

### 9. LLMOps notebook plan

`study/llmops/notebooks/M5_error_analysis_ops.ipynb`: error analysis on traces the way an observability team does it.
- **Framework build:** no LLM chain. Traces are loaded from the local JSONL into Phoenix (OpenInference spans) for browsing. Open codes are attached as **annotations** (Phoenix locally; LangSmith feedback for Corpus D only), and bucket labels become span attributes. Maps to lesson steps 3–5.
  - **Default to name:** platform "auto-evals" and clustering views suggest categories. In this course they are hypotheses only (`trace-data-analysis`).
- **External calls:** none. Optional counterfactual reruns reuse M3's cached oracle and closed-book answers. Replay-only.
- **Tracing:** the source is the v0 trace set. Every annotation carries the labeller, rubric version and timestamp.
- **Dataset and evaluators:**
  - Bucket definitions as code evaluators (0/1 per trace).
  - Confirmed failures → new items in the next dataset version (M1), tagged `regression` → T1/T2 tests (M4).
- **Experiment against the previous version:** bucket counts for v0 now. From v1 onward, the same evaluators show which buckets shrank: the evidence for the per-technique gate.
- **Cost / latency:** none for analysis. The tool reports the reading time per trace (self-timed) to plan later rounds.
- **Versioning:** `taxonomy_v1.md` (bucket names and definitions), versioned like prompts. A changed definition is a new version, and counts are recomputed.
- **Monitoring and feedback:**
  - The monitor page shows bucket counts per version and the share "unmapped".
  - Alert when "unmapped" rises above 10%, or when a closed bucket reappears.
  - Apply-it runs on Yash's documents feed new candidate codes (foundation §8.4).
- **Lifecycle:** Analyze (the start of every loop). Its output selects Phase 4–7 cards.
- **Skills:** `error-analysis`, `trace-data-analysis`, `human-review-interfaces`, `evals-foundations`, `llm-observability`.

### 10. Tools, frameworks, libraries and LLMs

The shared rows are in M1 §10. M5's own rows:

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Cross-tabs, counts, IQR flags | `pandas` | 3.0.6 | yes | yes | — | BSD-3 | yes |
| Pareto, 2×2 and saturation charts | `plotly` | 7.1.0+ | yes | yes | — | MIT | yes |
| Trace browsing and annotations (local) | Phoenix server via `uvx` + `arize-phoenix-otel` | 20.19.0 / 0.17.2 | no | yes | $0 | ELv2 / Apache-2.0 | yes |
| Coding sheet | the labelling-helper page (shared with M3), or CSV in the C6 lab | — | — | yes | $0 | ours | yes |
| LLM | **none**. An AI assistant may search, filter and plot traces; it never writes codes or causes (AE Ch11) | — | — | — | 0 calls | — | yes |

**Install lines:** none beyond the shared LLMOps rows.
**Keys:** none.

### 11. Open questions for Yash (preferences only)

- For open coding, would you rather work in the C6 lab table (Markdown in the notebook) or in the labelling helper page (decision 5), which can show the trace beside the note? **notebook / helper**

---

## Phase-level notes

1. **Teaching order inside the phase.** 02 orders the phase M1 → {M2, M3} → {M4, M5}. The research supports it, with two adjustments:
   - teach a **κ bridge in M1** (or move κ out of M1, M1-E3);
   - teach the **statistics bridge once in M4** and point back from M1's and M3's interval mentions, so that Wilson, the bootstrap and the exact tests are defined in one place.
2. **Prerequisite reality.**
   - Phase 3 needs Gate B (BL-1: v0 runs end to end). The tracker shows P2–P7 and C1–C7 `not_started`, so every Phase 3 lesson carries bridges (snapshot and offsets, Hit/MRR, traces).
   - The study kit can be written now (D-31), but the M3 pilot, the M4 flip-rate lab and M5's counts need v0 traces.
   - Until then the verify notebooks use the 10 verified seeds and offline retrieval, and say so.
3. **Corpus T timing.**
   - Gate 2→3 needs v0 on Corpus T, and 06 §10 defers T's eval set to v1.1.
   - The research says decisions on Corpus D are weak: a public PDF, general knowledge, easy synthetic items [S23, S26].
   - Recommendation: build a small T eval set (≥ 20 items with the same protocol) inside Phase 3 as soon as DEC-3 is chosen, so that M5's first bucket table covers both corpora. This is a planning note, not a gate change.
4. **Plan changes that need Codex (D-class):**
   - M3-E5, certifying on both class-wise rates with κ report-only;
   - M3-E6, resampling p_obs in the end batch;
   - M5-E6, dev-only error analysis;
   - M4-E3, labelling the bootstrap as approximate and leading with the exact test (wording only).
   - These join the ext review's §7 rows 4–23, which are still unapplied.
5. **Unowned book ideas** (gap 3):
   - sampling consistency → V4;
   - the noise-ratio sweep → V4 or an X-phase card;
   - BLEU/ROUGE/BERTScore → M3 Full only;
   - MAP → M2 bridge;
   - structured output → M3 core (D-22).
6. **Effects on other phases:**
   - The M3 structured-output lesson is reused by I4, V2 and A1–A3 graders (03 note).
   - M4's flip rate sets the T2 tolerance (06 §9.6) and RK-17.
   - M5's buckets gate R5 and S1 (add the multi-hop/global bucket, M5-E3).
   - M2's per-category CE@k is the primary detector for every Phase 4–7 card (03 §6.4).
7. **The LLMOps track for Phase 3** follows foundation §12's row, `3 · M1–M5`: almost no LLM calls (≈ 100–150 Groq calls in total, ≈ $0.05). The LangSmith view always runs with `upload_results=False`, and the T1 harness plus the flip-rate lab (record mode) start the CI story. The judge path is built and frozen, with **zero** judge calls until the end batch (D-10).
8. **The empty `.deepeval/` folder at the workspace root** (dated 2026-10-08).
   - It is consistent with deepeval having been imported once. The upstream `evaluation/evalute_rag.py` imports it (L19–L21), and deepeval writes `.deepeval/` in the working directory [S45]. Who ran it is unknown, and the folder holds no files.
   - The risk that matters: on import, deepeval **loads `.env` from the working directory** and phones home unless `DEEPEVAL_TELEMETRY_OPT_OUT=1`.
   - Never import upstream evaluation code from `rag_learning/`. If an upstream notebook is ever read by running it, set `DEEPEVAL_DISABLE_DOTENV=1` and `DEEPEVAL_TELEMETRY_OPT_OUT=1` first. The folder can be deleted by Yash; this session did not touch it.
9. **Existing reference code.** `contracts_check.py` already implements the core Phase 3 maths and passes 145/145. The `ragkit/eval/*` modules planned in 06 §10 should import nothing from it (it is a checker); they should be cross-checked *against* it in T1.

---

## Sources

Opened on 2026-10-17 by the research helpers or by Claude. "Verified" means the page was opened and the fact checked on it. Book and AE citations are in the text; they are local and were read directly.

**Generation metrics and judges**
1. [S1] Es, James, Espinosa-Anke, Schockaert, "Ragas: Automated Evaluation of Retrieval Augmented Generation", arXiv 2309.15217 — https://arxiv.org/abs/2309.15217 — verified
2. [S2] Saad-Falcon, Khattab, Potts, Zaharia, "ARES", arXiv 2311.09476 — https://arxiv.org/html/2311.09476 — verified
3. [S3] Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", arXiv 2306.05685 — https://arxiv.org/html/2306.05685 — verified
4. [S4] Wang et al., "Large Language Models are not Fair Evaluators", arXiv 2305.17926 — https://arxiv.org/abs/2305.17926 — verified
5. [S5] Min et al., "FActScore", arXiv 2305.14251 — https://arxiv.org/html/2305.14251 — verified
6. [S6] Gao, Yen, Yu, Chen, "Enabling Large Language Models to Generate Text with Citations" (ALCE), arXiv 2305.14627 — https://arxiv.org/html/2305.14627 — verified
7. [S7] Rajpurkar et al., SQuAD (arXiv 1606.05250) and SQuAD 2.0 (arXiv 1806.03822); official script https://raw.githubusercontent.com/rajpurkar/SQuAD-explorer/master/evaluate-v2.0.py — verified (human F1 89.5 UNVERIFIED on the abstract page; it appears in the paper text read by the M1 helper)
8. [S8] Panickssery, Bowman, Feng, "LLM Evaluators Recognize and Favor Their Own Generations", arXiv 2404.13076 — https://arxiv.org/html/2404.13076 — verified (venue UNVERIFIED)
9. [S9] Thakur et al., "Judging the Judges", arXiv 2406.12624 — https://arxiv.org/html/2406.12624 — verified
10. [S10] Shankar et al., "Who Validates the Validators?", arXiv 2404.12272 — https://arxiv.org/html/2404.12272 — verified (UIST 2024 venue UNVERIFIED)
11. [S11] Ru et al., "RAGChecker", arXiv 2408.08067 — https://arxiv.org/html/2408.08067 — verified
12. [S12] Pradeep et al., "Initial Nugget Evaluation Results for the TREC 2024 RAG Track with the AutoNuggetizer Framework", arXiv 2411.09607 — https://arxiv.org/html/2411.09607 — verified
13. [S13] judgy — https://github.com/ai-evals-course/judgy (README, `src/judgy/core.py`) and https://pypi.org/project/judgy/ — verified
14. [S14] Manakul, Liusie, Gales, "SelfCheckGPT", arXiv 2303.08896 (EMNLP 2023) — https://arxiv.org/abs/2303.08896 — verified (abstract; no numbers on the page)
15. [S15] Cuconasu et al., "The Power of Noise: Redefining Retrieval for RAG Systems", arXiv 2401.14887 — https://arxiv.org/abs/2401.14887 — verified (abstract; SIGIR 2024 venue inferred from DOI 10.1145/3626772.3657834, UNVERIFIED)

**Eval sets, retrieval labels and failure analysis**
16. [S16] Thakur et al., "BEIR", arXiv 2104.08663 — https://arxiv.org/abs/2104.08663; format wiki https://github.com/beir-cellar/beir/wiki/Load-your-custom-dataset; TREC qrels format https://trec.nist.gov/data/qrels_eng/ — verified
17. [S17] Smith & Troynikov, "Evaluating Chunking Strategies for Retrieval" (Chroma, 2024) — https://www.trychroma.com/research/evaluating-chunking — verified
18. [S18] Rajpurkar, Jia, Liang, "Know What You Don't Know: Unanswerable Questions for SQuAD", arXiv 1806.03822 — verified (PDF text)
19. [S19] Barnett et al., "Seven Failure Points When Engineering a Retrieval Augmented Generation System", arXiv 2401.05856; CAIN 2024 programme page https://conf.researchr.org/details/cain-2024/cain-2024-call-for-papers/5/Seven-Failure-Points-When-Engineering-a-Retrieval-Augmented-Generation-System — verified
20. [S20] Husain, "Using LLM-as-a-Judge For Evaluation: A Complete Guide" (2024, updated 2026) — https://hamel.dev/blog/posts/llm-judge/ — verified (practitioner source; binary labels with critiques, TPR/TNR validation)
21. [S21] Yang et al., "CRAG – Comprehensive RAG Benchmark", arXiv 2406.04744 — https://arxiv.org/html/2406.04744v2 — verified
22. [S22] Chen, Lin, Han, Sun, "Benchmarking Large Language Models in Retrieval-Augmented Generation" (RGB), arXiv 2309.01431 — https://arxiv.org/html/2309.01431 — verified
23. [S23] Rahmani et al., "Synthetic Test Collections for Retrieval Evaluation", arXiv 2405.07767 — https://arxiv.org/html/2405.07767 — verified (τ values as rendered on the HTML page)
24. [S24] de Lima et al., "Know Your RAG: Dataset Taxonomy and Generation Strategies for Evaluating RAG Systems", arXiv 2411.19710 — https://arxiv.org/html/2411.19710 — verified
25. [S25] Ribeiro, Wu, Guestrin, Singh, "Beyond Accuracy: Behavioral Testing of NLP Models with CheckList", arXiv 2005.04118 — verified (best-paper status UNVERIFIED)
26. [S26] Sainz et al., "NLP Evaluation in trouble", Findings of EMNLP 2023 — https://aclanthology.org/2023.findings-emnlp.722/ — verified
27. [S27] Dror, Baumer, Shlomov, Reichart, "The Hitchhiker's Guide to Testing Statistical Significance in NLP", ACL 2018 — https://aclanthology.org/P18-1128 — verified
28. [S28] McHugh 2012, "Interrater reliability: the kappa statistic" — https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/; Artstein & Poesio 2008, "Inter-Coder Agreement for Computational Linguistics" — https://aclanthology.org/J08-4004/ — verified
29. [S29] Husain & Shankar, "AI Evals FAQ" (2026) — https://hamel.dev/blog/posts/evals-faq/ — verified (practitioner source)

**Statistics and experimental discipline**
30. [S30] Bowyer, Aitchison, Ivanova, "Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints", arXiv 2503.01747 (ICML 2025) — verified (abstract)
31. [S31] Number checks (a)–(e) in M4 §5–§7, derived with the Python standard library by the M4 helper (scratchpad `m4/checks.py`) — verified by derivation
32. [S32] Koehn 2004, "Statistical Significance Tests for Machine Translation Evaluation", EMNLP — https://aclanthology.org/W04-3250 — verified
33. [S33] Berg-Kirkpatrick, Burkett, Klein 2012, "An Empirical Investigation of Statistical Significance in NLP", EMNLP-CoNLL — https://aclanthology.org/D12-1091 — verified
34. [S34] Card et al. 2020, "With Little Power Comes Great Responsibility", EMNLP — https://aclanthology.org/2020.emnlp-main.745 — verified
35. [S35] Miller 2024, "Adding Error Bars to Evals", arXiv 2411.00640 — https://arxiv.org/abs/2411.00640 — verified
36. [S36] Brown, Cai, DasGupta 2001, "Interval Estimation for a Binomial Proportion", Statistical Science 16(2) — abstract via https://asaip.psu.edu/?p=677 — abstract verified; full text UNVERIFIED
37. [S37] statsmodels `mcnemar` (0.15.0), SciPy `binomtest`, `bootstrap` (1.18.0), NumPy `percentile` (2.5) docs — https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html, https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html, https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html, https://numpy.org/doc/stable/reference/generated/numpy.percentile.html — verified
38. [S38] Dwork et al. 2015, "The reusable holdout", Science 349 — via https://research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/ (publisher page 403); Recht et al. 2019, arXiv 1902.10811 — verified (abstract or summary only)
39. [S39] Sclar et al., "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design", arXiv 2310.11324 (ICLR 2024) — verified (abstract)
40. [S40] Atil et al. 2024, "Non-Determinism of 'Deterministic' LLM Settings", arXiv 2408.04667 — verified (abstract)
41. [S41] He / Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference" (2025-09-10) — https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ — verified
42. [S42] Wu, Ribeiro, Heer, Weld, "Errudite: Scalable, Reproducible, and Testable Error Analysis", ACL 2019 — https://aclanthology.org/P19-1073/ — verified
43. [S43] Saunders et al. 2018, "Saturation in qualitative research", Quality & Quantity 52(4) — https://pmc.ncbi.nlm.nih.gov/articles/PMC5993836/ — verified. Corbin & Strauss 1990: metadata only (Crossref), content UNVERIFIED

**Also checked by the helpers, not cited above:** Bouthillier et al. 2021 (MLSys, abstract), Madaan et al. 2024 (arXiv 2406.10229, abstract), Holm 1979 (via Wikipedia and the statsmodels `multipletests` docs; original not read).

**Libraries and provider docs** (checked by the library helper on 2026-10-17)
44. [S44] PyPI JSON API (`https://pypi.org/pypi/<name>/json`) for every package in the §10 tables: versions, upload dates, licences, `requires_dist` — verified
45. [S45] ragas v0.4.3 source (`_analytics.py`, `evaluation.py`, `metrics/__init__.py`), https://raw.githubusercontent.com/vibrantlabsai/ragas/v0.4.3/src/ragas/; deepeval 4.2.8 wheel source (`telemetry/client.py`, `key_handler.py`, `test_run/*.py`, `config/settings.py`) and https://deepeval.com/docs/data-privacy; trulens 2.14.0 wheel source — verified (ragas writing `uuid.json` when opted out is inferred from the code, UNVERIFIED)
46. [S46] ir-measures and pytrec-eval-terrier docs (https://ir-measur.es/en/latest/measures.html), ranx metrics (https://amenra.github.io/ranx/metrics/), statsmodels 0.15.0 (`mcnemar`, `proportion_confint`, `cohens_kappa`), local `inspect` of scipy 1.18.1 and scikit-learn 1.9.1 — verified
47. [S47] LangSmith: https://docs.langchain.com/langsmith/pytest, `/local`, `/summary`, `/manage-datasets`, plus langsmith 0.14.4 wheel source — verified (behaviour with no API key UNVERIFIED); Label Studio 1.23.2 settings source and https://labelstud.io/guide/install; https://docs.argilla.io/latest/getting_started/quickstart/ — verified
48. [S48] Groq structured outputs and model page: https://console.groq.com/docs/structured-outputs, https://console.groq.com/docs/model/openai/gpt-oss-20b; Cohere models, structured outputs and chat reference: https://docs.cohere.com/docs/models, https://docs.cohere.com/docs/structured-outputs, https://docs.cohere.com/reference/chat — verified (temperature 0 and `response_format` on the reasoning model UNVERIFIED)
49. [S49] `claude-api` skill (bundled; price table cached 2026-10-06): Claude model ids and prices — read locally
