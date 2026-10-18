# Phase 8 research: Reliability and grounding

**What this is:** the research and gap audit for Phase 8 (V1, V2, V3, V4), done 2026-10-18 by Claude with five research helpers.
**What this is not:** lessons or code. Nothing in the course was changed, nothing was installed, and no LLM, embedding, rerank or tracing API was called.

**How much could be checked in this session.** Read this before trusting any citation.
- **Not in this checkout:** `CLAUDE.md`, `.claude/skills/`, `upstream/` (the two MIT repos and the interview guide), the book PDFs and the AI Eval book.
  - So **every book page and every repo-notebook cell below is copied from 02, 03, 04, 01, the C4/C5/P7 concept files or the external-resources review, and is UNVERIFIED here.**
  - No book text was read, so no book wording can have been copied.
  - Interview items marked `AIQ …` come from the external-resources review (2026-10-09), not from the interview repo itself.
- **Blocked by the network policy:** arXiv, the ACL Anthology, Hugging Face, Nature, OpenReview, `console.groq.com`, `docs.langchain.com`, `docs.cohere.com`. I did not try to get around it.
  - **A paper counts as verified here only when its official code repository was opened** (README, code or results file).
  - Numbers seen only in search-result summaries are marked **snippet only**.
- **Opened and checked:**
  - GitHub source and READMEs of ALCE, MiniCheck, RAGTruth, CRAG (paper code and Meta's benchmark), Self-RAG, LettuceDetect, UMBRELA, SelfCheckGPT, semantic entropy, FActScore, TRUE, FactCC, FairEval, Judging-the-Judges, LLM-judge-reporting, Sufficient Context, AbstentionBench (with its results CSV), RGB and OR-Bench.
  - Library source: the SQuAD 2.0 scorer in `huggingface/evaluate`, ragas faithfulness, TruLens RAG templates, NeMo Guardrails fact-checking docs, Guardrails AI provenance, LangGraph RAG examples and `_config.py`, `langchain-core` `chat_models.py`, `langchain-groq`, `langsmith` 0.14.4, `arize-phoenix-evals` 3.9.0, the `groq` 1.7.0 SDK, statsmodels `inter_rater.py`, scipy `_binomtest.py`, `judgy`.
  - Docs: Anthropic's citations, structured-outputs, pricing and reduce-hallucinations pages; Cohere's rerank best-practices page (from its docs repository on GitHub).
  - The PyPI JSON of every package named below.
- **Project skills** (`rag-evaluation`, `llm-as-judge`, `judge-validation`, `error-analysis`, …) were not on disk. I used their methods as `LLMOPS_FOUNDATION.md` states them.
- **Numbers marked "derived"** were computed in this session (hand arithmetic, or small numpy scripts in the scratchpad). They are not measurements of the course pipeline.

---

## Summary (read this first)

**The 5 most important gaps across the phase**
1. **"Supported" is not defined at the course's own unit, and the 06 citation metrics are not ALCE's.**
   - A `[doc:page]` label resolves to one or more chunks (C5 D.5). After Phase 7, a label may resolve to a merged window that crosses a page.
   - 06 §7.4 counts a citation as correct only if it supports its sentence *on its own*, and counts a sentence as recalled if *one* citation supports it. ALCE instead uses **joint** support for recall and a **leave-one-out** test for precision (ALCE `eval.py`, verified [1]).
   - On the multi-hop seed D-007, a correct answer must cite p.10 *and* p.29. Under 06's rule both citations are "unsupported" on their own, so citation precision is 0 for a perfect answer (derived).
   - V1 must fix the definitions and the unit (claim × resolved chunks) before anything is measured.
2. **The labels that Phase 8 measures against do not exist yet, and the data are too small for its own rules.**
   - V2 needs human relevance labels per (question, chunk) pair: about 55 × 4 = 220 pairs per run (derived), plus claim-level groundedness labels.
   - V4 needs at least 30 failure units per failure class, because a class of 10 certifies only at 10/10 (derived, Wilson).
   - V3 needs at least 15 unanswerable items with at least 5 in dev before any threshold claim (06 §8.4), but 06 §6.2 targets only 8.
   - So M1 must add unanswerables, and V4 needs a code-built challenge set (swapped numbers, swapped citations, negations). Natural v0 outputs on Corpus D will contain too few failures.
3. **Exact-string abstention undercounts refusals, and the default model is the kind that abstains least.**
   - RGB asked for a fixed refusal sentence, the same design as v0. ChatGPT used the exact string in 24.67% of cases, while an LLM judge found refusals in 45.00% (RGB, numbers snippet only [35]).
   - In AbstentionBench, reasoning-tuned models abstain less than their base models (derived from the results CSV: 0.475 vs 0.668 and 0.441 vs 0.731 mean recall [34]). The course default `gpt-oss-20b` is a reasoning model. Whether the effect holds for it is UNVERIFIED, so treat it as a hypothesis to test.
   - V3 must classify every answer three ways (exact refusal, paraphrased refusal, hedge plus answer), not two.
4. **Phase 8's call counts are understated, and its loops are unbounded by default.**
   - 06 v5.0 and the foundation's application map both say "+1–2 calls per query". Per-chunk relevance grading plus one groundedness check adds **k + 1 = 5** calls at k = 4, plus 2 more per regeneration (derived; matches 04 DV-12).
   - The per-chunk arm is about 180K tokens per run, nearly a full day of Groq's listed 200K-token quota (derived; plan UNVERIFIED).
   - LangGraph's default recursion limit is now **10,007**, not the 25 many tutorials assume (langgraph 1.2.12 source, verified [23]). The official self-RAG and agentic-RAG examples have no retry counter [22].
   - Every V2 graph needs an explicit attempt counter.
5. **Four different things are taught as one, and the course has no test for the fourth.**
   - The four are: a pointer is valid (C5's subset check), the cited text supports the claim (V1), the model actually used that text (faithfulness of attribution), and an explanation of why a chunk was retrieved (Ch19).
   - C5's toy T19 already shows the first passing while the second fails.
   - Research adds the third: a correct citation can be post-hoc. Wallat et al. call this post-rationalization, at up to 57% in an adversarial setup (snippet only [13]).
   - LLM explanations of their own reasoning can leave out the real cause (Turpin et al., repo verified [11]).
   - V1 needs one counterfactual probe (remove the cited chunk; does the answer change?) and must teach Ch19 as a critique target.

**Also worth knowing**
- **A score threshold cannot separate the course's own seeds.** On the v0 MiniLM index, unanswerable D-010 has rank-1 cosine 0.5196, higher than 5 of the 8 answerable seeds (C4 D.5). Any top-1 threshold high enough to abstain on it would also wrongly abstain on those 5 (derived).
  - Cohere says its own rerank scores depend on the query and are for ranking. Its threshold recipe needs 30–50 borderline query–document pairs [44].
  - A sufficiency check is the better signal. In Sufficient Context [32], a sufficiency autorater reached 0.93 accuracy on 115 labelled items (Gemini 1.5 Pro). Even so, "insufficient" did not mean "will be wrong": models were still correct up to about 35% of the time.
- **Local checkers make V1 and V2 cost no API calls.**
  - `transformers` 5.19.0, `torch` 2.14.1 and `sentence-transformers` 6.1.0 are already in the lock.
  - An NLI cross-encoder (`cross-encoder/nli-deberta-v3-base`, 90.04 MNLI-mismatched accuracy [8]) or HHEM-2.1-Open [7] runs on CPU with only a model download.
  - Pitfall: the sentence-transformers NLI heads output labels in the order **contradiction, entailment, neutral** [8].
- **Anthropic Citations guarantees valid pointers, not support** [9]. It returns `cited_text` that really is in the document. It does not check that the claim follows from it, and it cannot be combined with structured outputs (HTTP 400).
- **Detectors are weaker than they look.** Best checkers sit near 75% balanced accuracy on natural claims (LLM-AggreFact, snippet only [5]). The fixed 0.5 cut-off is not right for every metric (TRUE [50]). SelfCheckGPT's NonFact AUC-PR of 92.50 must be read against a random baseline of 72.96 [46].

**Tools to add, across the phase** (details in each concept's §10)
- **Nothing new for the lessons and verify notebooks.**
  - Already locked: `scipy` 1.18.1 (Wilson and exact intervals, bootstrap), `scikit-learn` 1.9.1 (`cohen_kappa_score`), `pydantic` 2.13.5 and `jsonschema` 4.26.0 (grader schemas), `transformers`/`torch`/`sentence-transformers` (local NLI), `numpy`, `pandas`, `plotly`.
  - Reference statistics already exist in `sources/verification/corrections/contracts_check.py`: `wilson`, `clopper_pearson_lower`, `cohens_kappa`, `kappa_bootstrap`, `ref_paired_bootstrap`.
- **Add (small): `rapidfuzz` 3.14.6** (MIT, 3.2 MB, no dependencies). It gives a fuzzy quote match that returns character offsets, for V1. `difflib` is the zero-install fallback.
- **Model downloads (no package):** one NLI checker for V1/V2, either `cross-encoder/nli-deberta-v3-base` (or `-small`), or HHEM-2.1-Open, which needs `trust_remote_code=True`. Decision 1.
- **From the foundation, for the LLMOps notebooks:** `langchain-core` 1.6.6, `langgraph` 1.2.12, `langsmith` 0.14.4, `arize-phoenix-otel` 0.17.2, plus `judgy` 0.1.0 for the end batch, which is better reimplemented (V4 §5).
- **Do not install:**
  - `minicheck`: **the PyPI name belongs to an unrelated model checker**. The real MiniCheck is git-only and pulls `openai`.
  - `lettucedetect` 0.2.3: pulls `openai` and a `python-dotenv==1.0.1` pin that conflicts with the project.
  - `selfcheckgpt`: pulls spacy, bert_score and openai.
  - `ragas`, `deepeval`, `trulens`, `nemoguardrails`, `guardrails-ai`, `arize-phoenix-evals` (ELv2; needs a provider LLM).
  - Read their prompts and source only.

**Decisions Yash must make** (each answerable in a word)
1. Local support checker for V1/V2: **NLI cross-encoder** (recommended: no remote code), **HHEM** (needs `trust_remote_code`), or **none** (LLM only)?
2. Grow the unanswerable set to at least 15 (at least 5 in dev) during M1, before v5.0? **Yes** is recommended. Without it, V3 can only report an exploratory curve.
3. V2 relevance grading: **per-chunk**, **batched** with shuffled order (recommended), or **cross-encoder threshold only**?
4. When the groundedness check fails: **abstain** (recommended), or **one regeneration**, then abstain?
5. Claude Citations as a V1 comparison arm: **defer** (recommended), or **include** when credits exist?

**Size of the build work** (S / M / L)
- **V1: L.** Per-sentence parsing, the definitions fix (joint support, label drift), a quote check, a local NLI check, ALCE-style metrics, the counterfactual probe and about 100 hand-labelled (sentence, citation) pairs.
- **V2: L.** Two graders, about 220 relevance labels per labelling round, a bounded regenerate-or-abstain graph, a four-arm ablation, and rate-limit planning.
- **V3: M.** Mostly deterministic, using stored scores. It needs the extra unanswerables, the three-way refusal classifier and the curve.
- **V4: M.** The statistics already exist in `contracts_check.py`. The work is the code-built challenge set, the labelling and the agreement report.

---

## Concept V1: Grounded answers and citation verification (E, project v5.0)

### 1. Sources checked

**Book pages (cited from 02/04/C5; UNVERIFIED here)**
- Ch3 p.8/14–p.9/14 (source highlighting, step 5: verbatim supporting segments returned with ids). This is the **primary** anchor (04 R-1, 08 D-28).
- Ch3 p.6/14 (even perfect context does not stop added claims; via C5 G.1).
- Ch19 p.3/10–p.7/10 (explanation steps and prompt), p.8/10 (attribution is separate from explaining a retrieval), p.7–9/10 (contrast).
- Ch22 p.7/19–p.8/19 (faithfulness by claim decomposition).
- App p.3/23, p.5/23: the summary credits Ch19 with claim tracing, which contradicts Ch19 itself (04 DV-39, DV-B9; C5 G.1).

**Repo notebooks and cells (cited from 02/04/C5; UNVERIFIED here)**
- `reliable_rag.ipynb` cells 22–23: highlighting with `PydanticOutputParser` and model `mixtral-8x7b-32768`; no substring check (DV-11).
- `explainable_retrieval.ipynb` cell 6 and `rs/explainable_retrieval.py:L17-L58`: the leading prompt "why is this relevant" (DV-39); `get_relevant_documents` is outdated.
- `graph_rag_local_attribution.ipynb` cells 7, 9, 17, 19: `[N]` parser that silently drops unknown tags; constant 0.9 confidence; Ollama.
- `evaluation/open-rag-eval-example.ipynb` cells 13–14: citation precision/recall as an offline metric. Phase 3 found that cells 8–14 print the first result rather than the matched query (static reading, M3-E3).

**Existing course files read**
- 02 V1 card and the REVIEWER NOTE; 03 stage 15 and the V1 row; 04 V1 row, R-1, Ch3 and Ch19 tables, §5 rows, DV-11 and DV-39.
- 06 §2.5, §3.3, §7.4 (citation precision, recall, page-hit), §8.3–8.4, the v5.0 card.
- 08 D-10, D-28, D-32.
- `concepts/C5_generation_citations.md` (D.4–D.7, G.1, G.2, H.3); `concepts/P7_grounded_prompting.md` (rules, D.7).
- Phase 7 research (X3 label drift, X3-E5/E6, deferred native-citations decision).
- The external-resources review (§5 rows); the tracker and misconception log; `LLMOPS_FOUNDATION.md`.
- Not present for V1: lesson, reading file, question file, lab, `sources/verification/V1/`.

**AE book sections:** none specific to V1. For citation labels per unit, 06 §8.4 and the `judge-validation` method (via the foundation) apply. Not checked here.

**Interview-repo items:** none listed for V1 in the external review. The questions in §5 are typical ones, not checked against the guide.

**External sources** (numbered as in the Sources list)
- Papers, through their repos: [1] ALCE; [3] Liu et al. verifiability; [4] AttributionBench; [5] MiniCheck; [11] Turpin et al.
- Model docs: [7] HHEM; [8] sentence-transformers NLI cross-encoders.
- Product docs: [9] Anthropic Citations; [10] LangChain citations how-to; [14] Anthropic reduce-hallucinations guide.
- Snippet only: [2] AIS; [6] Godbole & Jia; [12] Jacovi & Goldberg; [13] Wallat et al.

### 2. Gap audit

Yash's progress (tracker, 2026-10-18): **P1 and O1–O3 are exposed**; M2, M3, M5 and R1 are exposed. **P7, C4, C5, M1, M4, X1–X3 and every V concept are not started.** So every bridge below is "not studied".

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **Pointer validity vs support**: cited ⊆ retrieved is a set test on labels | the whole lesson | C5 D.5–D.7 (T19) | C5 | No | bridge | Open with T19: it passes the subset check and is unsupported. |
| 2 | **The claim unit**: sentence, or atomic claim | what is checked | 06 §7.4 says "sentence"; Ch22 says "claims" | V1 (M3 for claims) | No | **core** | Use the sentence as the unit in v5.0. Split multi-claim sentences only in Full (decomposition errors, [49]). |
| 3 | **Sentence splitting with citation tags** (`… 2015 [climate:10].`) | parsing | C5 D.6 heuristic (tag after the full stop belongs to that sentence) | C5 | No | bridge | Reuse C5's rule; add abbreviations and decimals ("1.2 °C") as tests. |
| 4 | **Label → resolved chunks**, and label drift after X1/X3 merges | which text is the premise | C5 D.5; Phase 7 X3 §label drift | C5 / X3 | No | bridge | The premise is the union of the resolved chunks *as shown in the prompt*. Use one label per page block (Phase 7 suggestion). |
| 5 | **Citation recall (ALCE)**: the joint set of cited passages entails the sentence | metric | 06 §7.4 (different rule) | V1 | — | **core** | Teach the ALCE rule, with D-007 as the case where it matters. |
| 6 | **Citation precision (ALCE)**: a citation is irrelevant only if it fails alone *and* the rest still entail without it | metric | 06 §7.4 (stricter rule) | V1 | — | **core** | A worked 2-citation example; compare with 06's per-citation rule. |
| 7 | **Citation page-hit** (cheap proxy against gold pages) | deterministic metric | 06 §7.4; M3 | M3 | No | bridge | Checks the *place*, not *support*; one line. |
| 8 | **Quote-based citation**: the model returns a verbatim quote; code checks it | verification step 1 | missing (DV-11: never checked) | V1 | — | **core** | Normalised exact match, then fuzzy alignment with offsets. A quote must be verbatim, so strictness is correct here. |
| 9 | **Entailment / NLI**: premise, hypothesis, three labels | verification step 2 | missing | V1 | — | **core** | One-read definition; label order trap [8]; the premise length limit (about 512 tokens, UNVERIFIED). |
| 10 | **Partial support** | labels, metric | missing | V1 | — | core | Liu et al. use full / partial / none [3]. Binary NLI cannot express it, so label it by hand. |
| 11 | **A score threshold** on the NLI output | decision | missing; MC-006 is open | V1 / V3 | No | core | Choose on dev labels, not 0.5 by default (TRUE [50]). |
| 12 | **Checker validation**: the checker's own false-accept rate | trusting V1 | V4 owns it | V4 | No | next | Measure the false-accept rate on about 100 labelled pairs; link to V4. |
| 13 | **Explanation ≠ attribution ≠ verification** | Ch19 critique | 02 REVIEWER NOTE; C5 G.1 | V1 | — | **core** | Three-column table with one example each. |
| 14 | **Correct ≠ faithful (post-rationalization)** | why a passing check is not proof of use | missing | V1 | — | core (Short: 2 lines; Full: probe) | Counterfactual probe: remove the cited chunk and re-ask. Needs 1 extra call per probed item. |
| 15 | **Answers from memory with a borrowed label** | T19; D-009 | C5 D.7; P7 D.7 | P7 / C5 | No | bridge | Corpus D is general knowledge, so "correct" is not "grounded" (Phase 3 gap 4). |
| 16 | **Abstentions carry no citations** | metric denominators | 06 §7.4 rules | M3 | No | bridge | Compute citation metrics only on non-abstained answers; print `n`. |
| 17 | **Structured output for quotes** (schema, validation, retry) | the quote arm | D-22: owner M3, not yet written | M3 | No | bridge | Pydantic `Citation(source_id, quote)`, as in the LangChain how-to [10]; validate; one logged retry. |
| 18 | **Provider-native citations** | alternative design | Phase 7 deferred to V1 | V1 | — | next (Full box) | Valid pointers and `cited_text`, not entailment; no structured outputs at the same time [9]. |

### 3. Quiz coverage

There is no `study/questions/V1_questions.md`. The questions it needs (titles only):
- **R-01** What is the difference between "cited ⊆ retrieved" and "supported"? (Use T19.)
- **R-02** ALCE's definitions of citation recall and citation precision.
- **R-03** Why a quote must be checked verbatim, but a claim must not be checked verbatim against the chunk.
- **A-01** Score a 3-sentence toy answer with 4 citations under ALCE and under 06 §7.4; explain the difference (D-007-style joint support).
- **A-02** Given NLI logits in contradiction/entailment/neutral order, label 4 pairs (label-order trap).
- **A-03** Resolve a `[climate:29]` citation to two chunks and choose the premise.
- **T-01** A legal-contract corpus: why fuzzy quote matching at about 90 fails on clause numbers, and what to do.
- **T-02** "Our Ch19-style explanations show the system is grounded." Critique this.
- **Interview:** "How would you verify citations cheaply in production?" (a tiered check, with the checker's own error measured).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| V1-E1 | 06 §7.4 citation precision and recall | Per-citation support and "≥ 1 supporting citation" differ from ALCE (joint entailment for recall; leave-one-out for precision; ALCE `eval.py` [1]). For a multi-hop sentence that needs two pages (D-007), 06 scores both correct citations as unsupported. | Adopt the ALCE rules, and name the checker used, because a small NLI model is not ALCE's T5-11B. |
| V1-E2 | 06 §7.4 "cited chunk(s)" | A page label resolves to several chunks (C5 D.5), and after X1 to merged windows. The premise is undefined. | Premise = the union of the blocks the label resolved to, as shown in the prompt. |
| V1-E3 | 02 V1 "Ext: none specific"; 01 Source C | ALCE, Liu et al. 2023, AttributionBench and MiniCheck are primary sources for exactly this concept. | Add Source C rows after verifying the papers. |
| V1-E4 | 03 §5 V1 row "NLI or judge checks cost extra calls" | A local NLI model costs CPU time, not API calls. Only an LLM checker costs calls. | Reword: "an LLM check costs calls; a local NLI check costs CPU time and its own error rate". |
| V1-E5 | 03 §5 V1 row "strict string matching rejects valid paraphrase" | True for claim-vs-chunk matching. For quote-based citation, a strict check is right, because the quote must be verbatim; paraphrase is handled by a separate entailment step. | Split the two cases. |
| V1-E6 | Gate 8→9 "every `[doc:page]` claim is checked against the retrieved spans" | After Phase 7 the label scheme changes (merged windows; Phase 7 X3-E5). | Say "against the blocks the label resolves to". |

### 5. What the research says

**ALCE** [1] (Gao et al., EMNLP 2023; code verified, paper snippet only)
- **The study:** LLMs answering with `[n]` citations on ASQA, QAMPARI and ELI5; citations scored by the TRUE NLI model (T5-11B).
- **The rules (from `eval.py`):**
  - Recall per sentence = 1 if the concatenated cited passages entail it; 0 if there is no citation.
  - Precision per citation: irrelevant only if it fails alone and the others still entail.
  - At most 3 citations per sentence are scored.
- **The result (snippet):** on ELI5, the best models lacked full citation support about half the time. The automatic metric agreed with human labels 85.1% (recall) and 77.6% (precision).
- **Its limits:** the judge is an 11B GPU model, and the labels are binary, so partial support is invisible.
- **For the project:** use ALCE's *rules* with a small local checker, call the result "ALCE-style", and report the checker's agreement with Yash's labels.

**Liu, Zhang and Liang 2023** [3] (repo verified; numbers snippet only)
- **The study:** human audit of four generative search engines.
- **The result:** on average 51.5% of sentences were fully supported and 74.5% of citations supported their sentence. Fluency and perceived utility were inversely correlated with citation quality.
- **The repo:** 11,037 statement–source judgements with full / partial / none labels, plus the minimal evidence that annotators pasted.
- **For the project:** copy the label scheme (full / partial / none, plus the evidence span). The partial class is about 17% of their test split (183 of 1,097, derived from the repo counts).

**AttributionBench** [4] (repo verified; numbers snippet only)
- **The study:** 7 attribution datasets merged into one binary task.
- **The result:** even a fine-tuned GPT-3.5 reached only about 80% macro-F1. Most errors came from fine-grained claim–evidence differences.
- **For the project:** a checker's error is not small; measure it.

**MiniCheck / LLM-AggreFact** [5] (repo verified; numbers snippet only)
- **The study:** small fact-checkers trained on synthetic data, scored on 11 grounding datasets.
- **The result:** Flan-T5-Large (770M) close to GPT-4. Bespoke-MiniCheck-7B led at 77.4% balanced accuracy.
- **Source facts:** documents are chunked and the score is the **max** over chunks; claims must be split into sentences first; the threshold is 0.5.
- **Its limits:** the 7B model has a commercial licence. The PyPI name `minicheck` is a different project.
- **For the project:** read-only. Its "max over chunks" design is a pitfall for evidence that spans two chunks.

**NLI cross-encoders** [8] and **HHEM-2.1-Open** [7]
- MNLI-mismatched accuracy: `nli-deberta-v3-base` 90.04, `-small` 87.55, `-xsmall` 87.77 (verified). They are trained on sentence pairs, not long passages.
- HHEM (snippet only): flan-t5-base, Apache-2.0, under 600 MB, about 1.5 s per 2k-token input on a CPU. Accuracy drops on long inputs. Loading needs `trust_remote_code=True` (seen in the ragas source).
- **For the project:** either fits the CPU budget. The NLI cross-encoder has no remote code. Test both on the same 100 labelled pairs if time allows.

**Godbole and Jia 2025** [6] (snippet only)
- Five factuality metrics on 11 datasets disagree with each other, and are biased against heavy paraphrase and against evidence that sits far away in the source.
- **For the project:** pick the checker on your own labels, not on a leaderboard.

**Anthropic Citations** [9] (verified)
- Plain-text documents are split into sentences and cited by character range. `cited_text` is not billed as output.
- Citations must be on for all documents or none. Combining them with structured outputs returns a 400.
- To make each RAG chunk one citable unit, send it as its own document.
- **For the project:** valid pointers by construction, but no entailment check, so V1's check still runs. A comparison arm only when credits exist (decision 5). No Groq equivalent was found (UNVERIFIED).

**LangChain citations how-to** [10] (v0.3 docs notebook, verified)
- Five patterns: cite ids by tool call; ids plus a verbatim quote (`Citation{source_id, quote}`); direct prompting; retrieval post-processing; a second annotation call.
- **It never checks in code that the quote exists.** That check is exactly V1's step 1.

**Explanations and faithfulness** [11][12][13]
- **Turpin et al. 2023** (repo verified). A biasing feature in few-shot prompts (the answer is always "(A)") changed answers, while the chain-of-thought explanations never mentioned it. Accuracy fell by up to 36% on BIG-Bench Hard.
- **Jacovi and Goldberg 2020** (snippet only). Faithfulness, meaning the explanation reflects the real reasoning, is not plausibility.
- **Wallat et al. 2024** (snippet only). A correct citation can be unfaithful when the model did not use that document. Up to 57% in an adversarial setup, so treat it as an upper bound.
- **For the project:**
  - A Ch19 explanation is generated text about a cosine ranking it never saw. It is plausible, not faithful.
  - The `gpt-oss-20b` reasoning field is not a citation rationale either.

**Current practice (my interpretation).**
- Production checks are tiered: quote existence and id validity first, a small local entailment model next, and an LLM only for the uncertain middle band and for claims with numbers or names.
- Anthropic's own guide asks the model to extract quotes first and retract unsupported claims [14].
- Thresholds are always tuned on the team's own labels.

**Pitfalls (with evidence).**
- Citations that exist but do not support: about 25% of real-engine citations [3].
- Partial support hidden by binary labels [1][3].
- Long premises cut off at the model's input limit; evidence that spans two chunks is missed by max-over-chunks [5].
- NLI label order [8].
- Multi-sentence claims fed whole [5].
- Paraphrase bias [6].
- Post-rationalised citations [13].
- Answers from memory that borrow a valid label (C5 T19).

**How to evaluate.**
- **Retrieval side unchanged.** Confirm CE@4 does not move.
- **Answer side:**
  - **Primary:** ALCE-style citation recall and precision by the local checker, *and* by Yash's labels on a fixed sample of about 100 (sentence, citation) pairs.
  - **Guards:** page-hit, invalid-citation rate, abstention rate.
  - **The checker's own scores:** agreement with the labels and its false-accept rate.
- **Baseline:** v4.x champion with C5's subset check only.

**Interview questions**
1. Recall vs precision for citations (ALCE)?
2. How do you verify citations cheaply in production (tiers, measured error)?
3. Is an LLM's explanation of why a document was retrieved an attribution? (No; it never saw the distances.)
4. The citation supports the claim, but the model ignored the document. Does it matter, and how would you detect it? (Counterfactual removal.)
5. Do native citation APIs solve hallucination? (Pointers, not entailment.)

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. A citation proves where the model pointed, not that the page says what the sentence claims.
2. V1 checks every cited sentence in two steps. First, if the model gave a quote, the quote must really occur in the cited block. Second, a small local entailment model, or a person, decides whether that block supports the sentence.
3. Citation recall asks whether each sentence is supported by all its citations together; citation precision asks whether each citation was needed.
4. The checker makes mistakes too, so we measure it on about 100 sentences we labelled ourselves before trusting its numbers.
5. An explanation of why a chunk was retrieved, like Ch19's, is a story about a similarity score; it is neither attribution nor verification.

**The theory in one read (11 linked ideas)**
1. **Pointer validity:** `cited ⊆ retrieved` (C5). Necessary, not sufficient.
2. **Unit:** a sentence s with citation set C(s), where each label resolves to blocks B(c).
3. **Premise:** P(s) = concatenation of B(c) for c ∈ C(s), in prompt order.
4. **Support:** support(s) = 1 if checker(P(s), s) ≥ τ.
5. **Citation recall:** CR = mean over factual sentences of support(s); a sentence with no citation scores 0.
6. **Citation precision:** for each c in C(s), c is irrelevant if checker(B(c), s) < τ **and** checker(P(s) − B(c), s) ≥ τ. CP = (citations not irrelevant) / (all citations).
7. **Quote check:** q verbatim in B(c) after normalisation; otherwise fuzzy alignment score ≥ θ, which returns offsets.
8. **NLI:** labels {contradiction, entailment, neutral}; support = P(entailment); the label order depends on the model.
9. **Threshold τ** chosen on dev labels; not 0.5 by default.
10. **Checker error:** false-accept rate = accepted ∧ human-unsupported / human-unsupported (V4 owns the full treatment).
11. **Explanation vs attribution vs faithful use:** three questions, three tests (none, entailment, counterfactual removal).

**Formula sheet items:** P(s); CR; CP with the leave-one-out rule; the quote-match rule; false-accept rate; page-hit.

**Step-by-step outline (running example: Corpus D, the course PDF)**
1. D-002 answer "The Paris Agreement was adopted in 2015 [climate:10]." Resolve → the p.10 chunk (C5). Quote "adopted in 2015" found verbatim. NLI says entailment. Supported.
2. D-009 toy T19, "The IPCC was established in 1988 [climate:29]." Valid pointer; resolves to two chunks; no quote can be found ("1988" is not in the PDF, 06 §6.7). The NLI checker should give neutral. Unsupported, flagged.
3. D-007 multi-hop answer citing p.10 and p.29. Each page alone fails; together they entail. ALCE recall = 1, precision = 1. 06's rule gives 0 (derived).
4. A distractor case from C4 D.4: an answer saying "1997" for D-002, citing the p.24 Kyoto chunk. The quote is found and NLI gives entailment for "adopted in 1997" but not for the Paris claim. Shows that support is about the sentence's own words.
5. The counterfactual probe on D-002: drop the cited chunk and re-ask. If the model still answers "2015" with a different citation, the original citation may be post-hoc (1 call; recorded once).

**Visuals that earn their place**
- **Four-gate diagram** (pointer valid → quote found → entailed → used). It shows that each gate catches a different failure, with T19 stopping at gate 2.
- **2-citation precision diagram:** the leave-one-out rule as two small Venn-style boxes. It shows why 06's rule fails D-007.
- **NLI score strip:** 20 hand-labelled pairs on a 0–1 axis, coloured by human label, with τ marked. It shows that the threshold is a choice.

**Full only:** atomic-claim decomposition and its errors [49]; partial support; Anthropic Citations mechanics; MiniCheck's max-over-chunks; the post-rationalization literature; AIS's "according to P, s" test [2].

### 7. Verify notebook plan

- **Recomputes:**
  - ALCE recall and precision on 6 hand-written toy answers (including T19 and the D-007 pair), matched against a pure-Python reference.
  - 06's rule on the same answers, as a side-by-side table.
  - Quote matching on 10 quotes: exact, case-changed, ellipsis, one wrong digit. Uses `difflib`; `rapidfuzz` if installed.
  - The NLI label-order trap: the same 4 pairs read with the right and the wrong label order.
- **Data:** the C5 lab's fixed v0 chunks for D-002 and D-009 (already in the C5 setup cell), plus the 06 §6.7 gold quotes.
- **Model:** one local NLI cross-encoder (decision 1). No API call. Offline after a single model download.
- **Plotly:** the NLI score strip with a τ slider.
- **Runtime:** under 2 minutes on CPU (about 40 short pairs; estimate).

### 8. Apply-it tool plan and real-world checklist

`study/tools/citation_check.py`
- **Inputs:** an answers JSONL (C5 records, or Yash's own app output), the chunk catalogue, optional gold pages, optional `--labels` CSV.
- **Outputs:** a per-sentence table (citations, resolved blocks, quote found?, support score, verdict), ALCE-style CR/CP, page-hit, and the checker's agreement with the labels if given. Runs fully offline.

| # | Check | Auto / manual |
|---|---|---|
| 1 | Every factual sentence has at least one valid citation | auto |
| 2 | Every citation resolves to a block that was in the prompt | auto |
| 3 | Labels that resolve to several blocks are reported | auto |
| 4 | Quotes (if any) occur verbatim; fuzzy matches are listed with offsets | auto |
| 5 | Support score per sentence against the union of its blocks | auto |
| 6 | Leave-one-out precision per citation | auto |
| 7 | Sentences with numbers, dates or names are always flagged for human review | auto (flag) + manual |
| 8 | Premise length versus the checker's input limit (truncation) | auto |
| 9 | The checker's false-accept rate on at least 50 of your own labelled pairs | manual (label), then auto |
| 10 | Abstentions excluded from the citation metrics, with `n` printed | auto |
| 11 | Paraphrased refusals are not scored as uncited answers (see V3) | auto + manual |
| 12 | 5 random "supported" sentences re-read by you each run | manual |

**Recommendation logic.**
- If the false-accept rate on your labels is above 10% (my threshold, to be set by you), do not report CR/CP from the checker; report the human sample only.
- If more than 20% of premises are truncated, switch to per-block checking with an OR over blocks, and say so.

### 9. LLMOps notebook plan

- **Framework build.** A plain-function chain is clearer than a graph here (foundation §9.1: no cycle):
  - `generate` (`CachedChatModel`) → `parse` → `resolve` → `quote_check` → `nli_check` → `score`.
  - The optional quote arm uses `with_structured_output(QuotedAnswer)`. The base `with_structured_output` calls `bind_tools` with `tool_choice="any"` and ignores `method=`/`strict=` [60], so the adapter must implement `bind_tools` and map "any" to Groq's "required" [59].
  - Strict `json_schema` support for `gpt-oss-20b` is UNVERIFIED (the docs were blocked), so keep a parse-and-retry fallback.
- **Defaults to name:**
  - LangChain's citation patterns never verify quotes [10].
  - Phoenix's `HallucinationEvaluator` now grounds against the *conversation*, not the retrieved context. Use `FaithfulnessEvaluator` if Phoenix templates are read [62].
- **Calls (cached):**
  - Generation reuses the v4.x recorded answers: 0 new calls.
  - The quote arm is one new generation run: about 55 Groq calls.
  - The counterfactual probe: about 10 calls.
  - The NLI check is local: 0 calls.
  - Total about 65 calls. Groq ≈ 65 × (1,300 × 0.075 + 400 × 0.30)/10⁶ ≈ **$0.014** (derived; assumed tokens).
  - Everything replays with no key.
- **Tracing:**
  - The JSONL trace gets a `verification` object per sentence (citations, resolved block ids, quote offsets, score, τ, verdict, checker model and revision).
  - In Phoenix, each check is an OpenInference `GUARDRAIL` span, and the metric step an `EVALUATOR` span (both kinds exist in semantic conventions 0.1.41 [62]).
  - LangSmith only for Corpus D.
- **Dataset and evaluators:**
  - The golden set plus a `citation_labels.csv` of about 100 (sentence, citation) pairs labelled full / partial / none.
  - Code evaluators: CR, CP, page-hit, invalid-citation rate, quote-found rate, truncation rate.
  - `langsmith.evaluate(..., upload_results=False)` with local `Example` objects. From the source, this looks runnable without a key [61]; not run.
- **Experiment:**
  - v4.x champion (subset check only) vs v5.0-V1 (verify and flag), and vs v5.0-V1 with removal of unsupported sentences.
  - Pre-registered: CR/CP on the human sample, with false abstention and correctness as guards.
- **Cost, latency, tokens:**
  - NLI time per sentence (p50/p95), added calls (quote arm), tokens.
  - Cost per question "if called" from the cached usage.
- **Versioning:** `prompts/answer_quotes_v1.txt`; checker model id and revision plus τ in `config.yaml`; label-file sha256 in the run summary.
- **Monitoring and feedback:**
  - Alerts: unsupported-sentence rate above the dev baseline plus a margin; quote-not-found above 0; truncation above 20%; checker model revision changed.
  - Each unsupported sentence goes to the M5 log as "unsupported claim" or "wrong page". If confirmed, it becomes a regression item.
- **Lifecycle:**
  - Analyze (`error-analysis`: read the flagged sentences).
  - Measure (`rag-evaluation`, `code-based-evaluators`; the checker validated with `judge-validation`).
  - Improve (prompt or quote arm).
  - dev → CI: a T1 test on the toy answers; a `replay` test on the notebook.
  - Monitoring (`ci-cd-evals`).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Parsing, quote check | `re`, `difflib` | stdlib | yes | yes | 0 | PSF | yes |
| Fuzzy quote alignment with offsets | `rapidfuzz` | 3.14.6 (2026-08-30) | no | yes | 0 | MIT | yes; 3.2 MB. Since 3.0 there is no default preprocessing, so pass `processor=utils.default_process` |
| NLI runtime | `sentence-transformers` `CrossEncoder` / `transformers` | 6.1.0 / 5.19.0 (lock) | yes | yes after download | 0 | Apache-2.0 | yes. **The lock's transformers 5.19.0 (2026-10-06) is newer than the 2-week rule**; 5.18.0 is the compliant pin |
| Support checker (option A) | `cross-encoder/nli-deberta-v3-base` (or `-small`) | HF model | no (download about 0.7 GB for base, snippet) | yes | 0 | Apache-2.0 (snippet) | yes; label order C/E/N; about 512 tokens (UNVERIFIED) |
| Support checker (option B) | HHEM-2.1-Open | HF model | no (< 600 MB, snippet) | yes | 0 | Apache-2.0 (snippet) | needs `trust_remote_code=True` (decision 1) |
| Read-only | MiniCheck (git), `lettucedetect`, TRUE T5-11B | — | no | — | — | Apache / MIT | **no**: PyPI name trap, pulls `openai`, GPU |
| LLM (quote arm, probe) | Groq `openai/gpt-oss-20b` | `GROQ_MODEL_ID` | — | no | about 65 calls ≈ $0.014 | — | yes (default) |
| LLM (optional) | Claude Haiku 5.5 `claude-haiku-5-5` | — | — | no | about 65 × (1,300 × 0.10 + 400 × 0.50)/10⁶ ≈ $0.021 | — | yes, when credits exist; structured outputs supported [63] |
| Native citations (comparison) | Claude Sonnet 5.5 + Citations | — | — | no | about 55 × (1,500 × 2 + 400 × 10)/10⁶ ≈ $0.39 per run | — | defer (decision 5) |
| Framework | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (LLMOps only) |
| Tracing | `langsmith` / local JSONL + `arize-phoenix-otel` | 0.14.4 / 0.17.2 | no | SDK yes / yes | free plan | MIT / Apache-2.0 | yes; Corpus D only for LangSmith |

```text
uv add rapidfuzz==3.14.6
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2   # from the foundation
```

Keys: `GROQ_API_KEY` (present); `ANTHROPIC_API_KEY` and `LANGSMITH_API_KEY` when used. The Hugging Face download needs no key.

### 11. Open questions for Yash (preferences only)
- Label scheme for the 100 citation pairs: **3 classes** (full / partial / none, recommended) or **binary**?
- When a sentence is unsupported: **flag it** in the answer (recommended for v5.0, keeps the answer comparable) or **delete it**?

---

## Concept V2: Reliable RAG: relevance grading and groundedness check (E, project v5.0)

### 1. Sources checked

**Book pages (cited from 02/04; UNVERIFIED here)**
- Ch3 p.4/14–p.5/14: relevancy grading; sketch p.5/14.
- Ch3 p.6/14–p.8/14: hallucination check and the flag-or-regenerate rule; sketch p.8/14.
- Ch3 p.9/14–p.10/14: the complete pipeline.
- Ch3 p.10/14–p.11/14: model choice.
- Ch3 p.11/14: "2–4 extra calls"; the table says 2–3 (04 DV-12).
- Ch13 p.12/13–p.13/13: grading vs reranking (03 §3.5; 04).

**Repo notebooks and cells (cited from 02/04; UNVERIFIED here)**
- `reliable_rag.ipynb` cells 6 (500-token chunks, k = 4), 14 (`GradeDocuments`, lenient prompt), 16 (filter loop), 18 (answer prompt "based upon your knowledge", DV-09), 20 (groundedness score printed, no branch, DV-10), 22 (highlighting).
- The model ids `llama-3.1-8b-instant` and `mixtral-8x7b-32768` are probably retired (D-04).
- The research helper read the same notebook's code on GitHub. It confirmed k = 4, `llama-3.1-8b-instant` for grading and generation, and that **the groundedness grader never sees the question**.
- Yash's own `prior_work/my way/reliable_rag` notebook (executed) is the fast-track evidence (02 V2 "FT: likely"). It is not in this checkout.

**Existing course files read**
- 02 V2 card and Phase 8 table; 03 stages 11 and 15, the V2 row, the "V2 ← V1" note, the structured-output REVIEWER NOTE; 04 V2 row, Ch3 table, DV-08 to DV-12.
- 06 v5.0 card, §7.4, §8.1–8.4, §9.5 (ablation template); 08 D-10, D-22, D-32.
- C5 (D.6 flags), P7 (D.7 permissive prompt), the misconception log (**MC-006** is V2's), the tracker (V2 application score 1, from O1-Q11), the external review (V2 T-item on NLI guardrails).
- Not present for V2: lesson, reading file, question file, lab.

**AE book sections:** none specific. M3 and V4 own the judge methods. Not checked here.

**Interview-repo items:** the external review's V2 T-item ("critique a guardrail design", SDG `13-reliability-and-safety/01-guardrails.md`). UNVERIFIED here.

**External sources:**
- Papers, through their repos: [15] CRAG; [16] Self-RAG; [17] RAGTruth; [19] LettuceDetect; [21] UMBRELA.
- Framework and library source: [22] LangGraph RAG examples and current docs; [23] LangGraph recursion limit; [24] ragas faithfulness; [25] TruLens RAG triad; [26] NeMo Guardrails fact-checking; [27] Guardrails AI provenance; [59] groq SDK; [60] langchain-core; [65] langchain-groq.
- Snippet only: [18] Lynx; [20] Thomas et al.; [28] AWS Bedrock; [29] Azure; [30] Panickssery et al.; [31] Tang et al. 2024.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **Two checkpoints at two stages**: a filter before generation, a verifier after it | the design | 03 stages 11 and 15 | V2 | — | **core** | One pipeline picture with both gates and what each can miss. |
| 2 | **A binary grader is a classifier with a fixed cut-off**, not a reranker | why not just R3 | 03 says "pointwise reranker with a binary label" | V2 / R3 | No | core | Correct the wording: with yes/no there is no ranking, only a filter. A reranker score plus a threshold is the cheap baseline. |
| 3 | **Confusion matrix of a grader** against span-derived gold (C4 `rel` from evidence spans) | measurement | M2 (`rel`); M3 (judge labels) | M2 / M3 | No (M2 exposed) | bridge | Gold relevance = the chunk overlaps a gold alternative. For unanswerables, every chunk is gold-irrelevant. |
| 4 | **Which error matters**: false rejects of gold chunks vs false keeps | decision | missing | V2 | — | **core** | Key safety number: recall on gold chunks; plus "only gold chunk dropped" and "zero chunks left". |
| 5 | **Strict vs lenient grader prompts** | why upstream filters little | DV-09 neighbour; not taught | V2 | — | core | The LangGraph/upstream prompt passes keyword overlap, roughly UMBRELA level ≥ 1 [21][22]. |
| 6 | **Structured output**: schema, enum, validation, retry on parse failure | every grader | D-22 (owner M3; not written) | M3 | No (M3 exposed) | bridge | `Literal["yes","no"]`; validate; one logged retry; count parse failures. Groq: `json_schema` strict support for gpt-oss-20b UNVERIFIED; `tool_choice` has no "any" [59]. |
| 7 | **Groundedness check = V1 at answer level** (claims vs kept chunks) | output gate | V1 | V1 | No | bridge | Reuse V1's checker. The answer-level verdict is "any unsupported sentence". |
| 8 | **The empty-context path** | after filtering | external review: X3 lab test (`no_context`) | X3 | No | bridge | No chunk survives → fixed abstention, no LLM call, reason `no_context`. Never score it as a correct abstention without logging (V3). |
| 9 | **Regenerate vs abstain, bounded** | after a failed check | DV-10; not taught | V2 | — | **core** | An attempt counter in state; at most 1 retry; then abstain (decision 4). |
| 10 | **Self-grading bias** | model choice | 06 §8.2 (judge) | M3 / V4 | No | bridge | Do not grade with the generator. Use a local checker, or another family (Haiku vs gpt-oss) [30]. |
| 11 | **Uncalibrated scores and fixed thresholds** | any score grader | MC-006 (open) | V2 / V3 | No | **core** | A 0–1 LLM score has no fixed meaning; choose the cut-off on dev labels (MC-006 correct model). |
| 12 | **Cost arithmetic**: calls = 1 + k + 1 (+2 per retry) | budget | 04 DV-12 | V2 / D2 | No | core | Derive 6 calls at k = 4, and the batched alternative (3 calls). |
| 13 | **Rate limits decide the time** | the per-chunk arm | foundation §6.3 | D2 | No | bridge | About 180K tokens per per-chunk run against a 200K/day listed quota (plan UNVERIFIED). |
| 14 | **Position bias in batched (listwise) grading** | the batched arm | missing | V2 | — | Full | Shuffle the chunk order and put ids in the schema [31]. |
| 15 | **The permissive answer prompt** | generation | P7 D.7; DV-09 | P7 | No | bridge | Keep the v0 grounded prompt; the upstream "based upon your knowledge" defeats the check. |
| 16 | **Abstentions game groundedness** | metric | missing | V2 / V3 | — | core | TruLens scores "I don't know" as fully grounded [25]. Report the abstention rate beside groundedness. |
| 17 | **Correct but not in the context** (RAGTruth `implicit_true`) | flags that look false | missing | V2 | — | Full | A grounded check *should* flag them; Corpus D is general knowledge. |
| 18 | **Adopt/reject per checkpoint** (ablation) | decision | 06 §9.5 | M4 | No | bridge | Four arms on the same cached retrievals. |

### 3. Quiz coverage

There is no `study/questions/V2_questions.md`. The questions it needs (titles only):
- **R-01** What does each checkpoint catch, and what can neither catch?
- **R-02** Why is a yes/no grader not a reranker?
- **R-03** Count the LLM calls per question for per-chunk grading at k = 4 with one retry.
- **A-01** Fill a grader confusion matrix from 12 labelled (question, chunk) pairs and compute precision, recall on gold, and "only gold chunk dropped".
- **A-02** The grader keeps 0 chunks for D-002. Trace what the v5.0 pipeline must do.
- **A-03** (MC-006 check) A teammate sets "relevance ≥ 0.7" from one run. What do you do instead?
- **T-01** (external review) Critique an NLI guardrail that checks the answer against a truncated whole context.
- **T-02** A medical corpus where answers must never come from memory: which checkpoint do you keep, and why?
- **Interview:** "How do you stop a self-correcting RAG loop from running forever?"

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| V2-E1 | 06 v5.0 "Cost: +1–2 LLM calls per query"; `LLMOPS_FOUNDATION.md` §12 row 8 "+1–2 calls/query" | Hypothesis (b) uses "an LLM relevance grade as in Ch3". Per chunk, that is k + 1 = 5 extra calls at k = 4 (6 in total), plus 2 per regeneration (derived; 04 DV-12 already counts 6). | State both arms: per-chunk +5; batched +2; each retry +2. |
| V2-E2 | 03 §2.2 "V2 ← V1" note and §3.5 | "A relevance grader is also a pointwise reranker that returns a binary label." A yes/no label gives no order. | "A pointwise classifier; it becomes a reranker only if it keeps a score." |
| V2-E3 | 04 V2 row and 02 V2 card: "Groq + Cohere implementation (closest to the learner's keys)" | The notebook needs `langchain-groq`, which conflicts with the project's `groq` 1.7.0 (foundation finding 4). Its model ids are probably retired. | Mark "read-only; rebuild on the adapter". |
| V2-E4 | Foundation §9.2 | Missing two framework defaults that V2 depends on: (a) LangGraph's `recursion_limit` default is 10,007 [23]; (b) `BaseChatModel.with_structured_output` ignores `method=`/`strict=` and needs `bind_tools`, sending `tool_choice="any"`, which Groq does not accept [59][60]. | Add both rows. |
| V2-E5 | 04 Ch3 table, row 4 | Says the groundedness check is "partial: prints the score only". The helper also found that the grader is never shown the question (upstream code). | Add that fact; it matters for "answers a different question" failures. |

### 5. What the research says

**CRAG** [15] (Yan et al. 2024; paper code verified, paper numbers snippet only)
- **The study:** a fine-tuned T5-large evaluator scores each (question, document) pair; two thresholds give three actions (Correct, Ambiguous, Incorrect).
- **From the code:**
  - PopQA thresholds 0.592 (upper) and −0.995 (lower); PubQA 0.5 and −0.915.
  - **Set-level aggregation:** Correct if *any* document reaches the upper threshold; Incorrect only if *all* fall below the lower one.
- **Results:** a 2026 reproduction (snippet only) got PopQA 54.4 vs 54.9 for the original and 51.4 for plain RAG. It also found that the evaluator leans on named-entity overlap.
- **Limits:** trained and tuned per dataset; uses web search.
- **For the project:** the upstream "drop every no" rule has no any-document guard. Add one: if the only gold-looking chunk is dropped, the system should know.

**Self-RAG** [16] (Asai et al., ICLR 2024; README verified)
- Trained reflection tokens (ISREL, ISSUP, ISUSE) weight a beam search. Defaults: w_rel 1.0, w_sup 1.0, w_use 0.5, retrieval threshold 0.2.
- It is not a hard filter, and it needs token probabilities.
- **For the project:** Groq does not support logprobs (SDK docstring [59]), so the prompted graders here are an imitation, as 03 says of A3.

**RAGTruth** [17] (Niu et al., ACL 2024; README verified, numbers snippet only)
- About 18K naturally generated RAG answers with word-level hallucination spans.
- Useful fields: `implicit_true` (correct but not in the context) and `incorrect_refusal`.
- Detector results (snippet): fine-tuned Llama-2-13B 78.7 answer-level F1; prompted GPT-4-turbo 63.4; gpt-3.5 52.9, with recall 92.3 but precision 37.1.
- **For the project:** prompted LLM checkers tend to over-flag. Measure precision, not only recall.

**LettuceDetect** [19] (2025; docs verified)
- ModernBERT token classifier with 4K context. RAGTruth answer-level F1 79.22 (large) and about 76–77 (base).
- Its v2 shows span-level F1 far below answer-level F1 (0.574 vs 0.818).
- **For the project:** answer-level "is anything unsupported" is easier than "which words". Read-only (dependency conflict, §10).

**UMBRELA** [21] (prompt verified) and **Thomas et al. 2023** [20] (snippet only)
- LLM relevance labels can match TREC assessors when the prompt is chosen against human data, but quality moves with small prompt changes.
- UMBRELA's 0–3 scale: 1 = related but does not answer, 2 = partly answers, 3 = dedicated and exact.
- **For the project:** label gold relevance on this scale, then binarise at ≥ 2, with ≥ 1 as a sensitivity check.

**LangGraph examples** [22][23] (code verified)
- Graders use `with_structured_output` with a binary score and a deliberately lenient prompt, one call per chunk.
- In self-RAG, "not supported" loops straight back to `generate` with **no counter**.
- The current agentic-RAG docs grade inside the conditional edge.
- The default recursion limit is **10,007** (`_internal/_config.py`, overridable by `LANGGRAPH_DEFAULT_RECURSION_LIMIT`); langchain-core's own config still says 25.
- The CRAG tutorial rewrites and searches if *any* chunk is graded "no", which is stricter than the paper's all-below rule.

**ragas faithfulness** [24] and **TruLens** [25] (source verified)
- **ragas:** an LLM splits the answer into statements; one NLI-style call gives each a 0/1 verdict against all contexts joined; score = supported / total. Two calls per answer; an `llm` must be passed. An HHEM variant swaps the second step.
- **TruLens:** groundedness scores statements 0–3, and scores "I don't know" at the maximum.

**Production guardrails** [26][27][28][29]
- **NeMo `self check facts`** (verified): one yes/no LLM call over the relevant chunks; below 0.5 the bot refuses. With reasoning models, running out of tokens before the verdict fails closed (blocked).
- **Guardrails AI `provenance_llm`** (verified): sentence-level, the top-3 nearest source chunks, then one LLM yes/no per sentence.
- **AWS Bedrock** (snippet only): separate grounding and relevance scores with user thresholds. **Azure** (snippet only): adds a reasoning mode that needs your own model.
- **For the project:** every product leaves the threshold to the user, which is MC-006 in product form.

**Bias evidence** [30][31] (snippet only)
- LLM judges recognise and favour their own outputs.
- Listwise prompts have position bias; shuffling and aggregating helps.

**Current practice (my interpretation).**
- Input-side grading is common in tutorials and rarer in production, where a reranker score with a threshold does the same job for one forward pass.
- Output-side checks are common. Products run them with a dedicated small model or one LLM call, always fail-closed, and with user-set thresholds.

**Pitfalls (with evidence).**
- A lenient grader barely filters [22].
- A strict one drops the only evidence; CRAG's any-document guard exists for this reason [15].
- Empty context after filtering.
- Unbounded loops [22][23].
- The permissive prompt (DV-09).
- Self-grading bias [30].
- Position bias in batches [31].
- Reasoning-model graders running out of `max_tokens` [26].
- Abstention gaming groundedness [25].
- Over-flagging by prompted checkers [17].

**How to evaluate.**
- **Relevance grader:** confusion matrix vs span-derived gold relevance. Report precision of "keep", recall on gold chunks, the share with zero chunks left, and the share where the only gold chunk was dropped.
- **Groundedness check:** "not grounded" is the positive class; report its precision and recall on human labels, with Wilson intervals (V4).
- **End-to-end:** the 06 §9.5 ablation (none / grader only / check only / both) on identical cached retrievals.
  - Answer side: correctness (EM/F1 where defined; human labels), unsupported-sentence rate (V1), abstention and false-abstention.
  - Cost side: calls, tokens, p50/p95.
  - Retrieval metrics only to confirm they did not change; CE on the final (filtered) context to show evidence lost.
- **Baselines:** a cross-encoder score with a threshold for relevance; a local NLI/HHEM check for groundedness.

**Interview questions**
1. Why grade chunks if you already rerank?
2. Which grader error is worse, and why?
3. How does RAGAS faithfulness work, and what does it cost?
4. How do you bound a self-correcting loop?
5. Why not let the generator check itself?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. Reliable RAG adds two checks: a grader before generation that throws away chunks that do not help, and a check after generation that the answer is supported by what was kept.
2. Each check is a classifier, so it makes two kinds of mistake. Throwing away the only good chunk is worse than keeping a useless one.
3. We measure both checks against our own labels and count what they cost: at k = 4, grading each chunk and checking the answer adds five model calls to one.
4. When the answer is not supported we abstain, or retry once and then abstain; a loop without a counter can run thousands of steps.
5. A checkpoint stays only if the ablation shows it improves answers by more than it costs.

**The theory in one read (10 linked ideas)**
1. **Two gates:** G_in(q, c) ∈ {keep, drop} per chunk; G_out(answer, kept) ∈ {grounded, not}.
2. **Gold relevance from spans:** rel(c) = 1 if c overlaps a gold alternative (M2's `rel`).
3. **Grader confusion matrix:** TP = keep ∧ rel, FN = drop ∧ rel, and so on; recall_gold = TP / (TP + FN).
4. **Evidence loss:** CE_final = CE on the kept chunks; ΔCE = CE@k − CE_final.
5. **Zero-context rate:** the share of questions with kept = ∅ → abstain with reason `no_context`.
6. **Groundedness check:** not_grounded = any sentence with support(s) = 0 (V1).
7. **Check quality:** precision and recall of "not grounded" vs human labels.
8. **Calls:** per-chunk N = 1 + k + 1 + 2r; batched N = 1 + 1 + 1 + 2r, where r = retries.
9. **Bounded control:** attempts ≤ 1 + r_max; then abstain.
10. **Adopt rule:** keep a gate only if the ablation shows Δ(answer metric) > 0 with an interval, at an acceptable Δcost.

**Formula sheet items:** recall_gold, precision_keep, ΔCE, zero-context rate, the call formula, the precision and recall of "not grounded".

**Step-by-step outline (running example: Corpus D)**
1. D-002 top-4 from C4: seq 69 (p.24, Kyoto), 68 (p.23), 27 (p.10, gold), 17. A lenient grader keeps all 4, including the Kyoto distractor that invites "1997". A strict grader keeps only seq 27. A wrong strict grader drops seq 27 too and leaves only distractors. Show all three outcomes as hand-made toy grades (not model outputs), and what each does to CE on the kept chunks.
2. D-010 (unanswerable): every chunk is gold-irrelevant. If the grader keeps p.6 "transport efficiency", the answer may invent a percentage.
3. The groundedness check on a toy answer containing a number that is not in the kept chunks → not grounded → abstain.
4. Count calls and tokens for one question in both arms (derived).
5. The ablation table shape from 06 §9.5, with empty cells.

**Visuals that earn their place**
- **Pipeline with two gates and a bounded loop:** where each error type enters, and the counter.
- **Call and token bar chart** for 4 arms (none, per-chunk, batched, check only): the cost of each gate.
- **Grader confusion matrix** as raw counts: why recall on gold is the number to watch.

**Full only:** CRAG's two-threshold, three-action evaluator and set-level aggregation; Self-RAG reflection tokens; RAGTruth `implicit_true`; position bias in batched grading; the product guardrail designs.

### 7. Verify notebook plan

- **Recomputes:**
  - The call and token arithmetic for k = 2, 4, 8 and r = 0, 1, in both arms.
  - Confusion matrices from a fixed toy label set (12 pairs).
  - recall_gold, ΔCE on the toy D-002 cases.
  - The zero-context path (a unit-test-style cell).
  - A bounded loop in plain Python that stops at r_max, with an assertion that an always-failing check ends in abstention after 1 + r_max attempts.
- **Data:** the C5 lab's fixed v0 chunks; hand-written toy grades and answers.
- **Calls:** none (a `FakeGrader` returns fixed labels). Offline.
- **Runtime:** under 30 s.
- **Plotly:** the call and token bars.

### 8. Apply-it tool plan and real-world checklist

`study/tools/grader_audit.py`
- **Inputs:** a JSONL of grader decisions (question id, chunk id, verdict, raw output, latency, tokens), gold relevance (from the span gold or a labels CSV), and optional groundedness labels.
- **Outputs:** confusion matrices with counts, recall_gold, the zero-context rate, the "only gold dropped" list, parse-failure rate, calls and tokens per question, p50/p95. A **keep / drop / inconclusive** verdict per checkpoint.

| # | Check | Auto / manual |
|---|---|---|
| 1 | The grader's recall on gold chunks, with a Wilson interval | auto |
| 2 | Questions where the only gold chunk was dropped (list with ids) | auto |
| 3 | Questions left with zero chunks, and what the pipeline did | auto |
| 4 | Parse failures and retries of the structured output | auto |
| 5 | `finish_reason = length` on grader calls (reasoning ran out) | auto |
| 6 | The groundedness check's precision and recall of "not grounded" on your labels | manual labels, then auto |
| 7 | The grader is not the generator (model id differs, or a local checker) | auto |
| 8 | The loop is bounded: maximum attempts observed ≤ 1 + r_max | auto |
| 9 | Abstention rate reported next to groundedness | auto |
| 10 | Calls and tokens per question versus the budget | auto |
| 11 | 10 dropped chunks re-read by you: were they really irrelevant? | manual |
| 12 | The answer prompt is the grounded one (no "your knowledge") | manual |

**Recommendation logic.**
- Drop the input grader if recall_gold < 0.95 (my threshold, to be set by you), or if it does not beat a cross-encoder threshold on the same pairs.
- Drop the output check if its "not grounded" precision is below 0.5, which would mean more needless abstentions than caught errors (my threshold).
- If an interval spans the threshold: inconclusive.

### 9. LLMOps notebook plan

- **Framework build: LangGraph**, because the flow has a branch and a bounded cycle (foundation §9.1).
  - **Nodes:** `retrieve` (cached retrieval) → `grade_documents` (per-chunk or batched) → `decide` (kept = ∅ → `abstain`) → `generate` → `check_grounded` → (grounded → END; not grounded and attempts < 1 + r_max → `generate`; otherwise → `abstain`).
  - **State:** question, chunks, grades, kept, answer, check verdict, `attempts`, `abstain_reason`.
  - **Pass `recursion_limit` explicitly** (for example 10) as well as the counter.
- **Mapped to the lesson:** G_in = `grade_documents`, G_out = `check_grounded`, the counter = idea 9.
- **Framework defaults to name:**
  - recursion limit 10,007 [23];
  - `with_structured_output` needs the adapter's `bind_tools`, sends `tool_choice="any"` (Groq wants "required"), and ignores `method`/`strict` [60][59];
  - `langchain-groq`'s own default is function calling, with strict mode only for json_schema on gpt-oss [65]; it is not installed (foundation);
  - the LangGraph tutorial prompt is lenient [22].
- **Calls per run (cached)**, about 55 questions, about 50 answered (assumed):

| Arm | Calls | Tokens (derived, assumed sizes) | Groq cost | Haiku 5.5 cost |
|---|---|---|---|---|
| Per-chunk grading | 220 | ≈ 121K (450 in + 100 out each) | ≈ $0.014 | ≈ $0.021 |
| Batched grading | 55 | ≈ 69K (1,100 in + 150 out) | ≈ $0.007 | ≈ $0.010 |
| Groundedness check | ≈ 50 | ≈ 60K (1,100 in + 100 out) | ≈ $0.006 | ≈ $0.008 |
| One retry on ~10% | ≈ 10 | ≈ 15K | < $0.002 | < $0.003 |

  - The per-chunk run with the check is about 180K tokens, roughly a day at the listed 200K TPD (plan UNVERIFIED), and at least 23 minutes at 8K TPM.
  - Plan it as a resumable run in `auto` mode.
  - Everything replays with no key.
  - Generation itself reuses recorded v4.x answers where the kept set did not change. A changed kept set is a cache miss, which is the point.
- **Tracing:**
  - Every node is a span, with the grade decisions per chunk (id, verdict, raw output, model, prompt version) and the branch taken.
  - Graders and checks are OpenInference `GUARDRAIL` spans [62]; `attempts` and `abstain_reason` go on the root span.
  - Phoenix locally; LangSmith for Corpus D only.
- **Dataset and evaluators:**
  - The golden set, plus `relevance_labels.csv` (UMBRELA 0–3 per (question, chunk), about 220 pairs; label once, reuse for every arm), plus claim or answer groundedness labels on about 50 answers.
  - Code evaluators: recall_gold, precision_keep, zero-context rate, ΔCE, parse-failure rate, attempts histogram, abstention, EM/F1, V1's CR/CP.
  - **No LLM evaluation judge (D-10).** The V2 grader is part of the system, not the judge.
- **Experiment:** the 06 §9.5 four-arm ablation vs v4.x champion and v0, on identical retrievals, pre-registered; the paired bootstrap on answer metrics; per-arm cost and latency.
- **Cost, latency, tokens:** calls per question (histogram), tokens per node, p50/p95 per node (grading in parallel vs serial), cost "if called".
- **Versioning:** `prompts/grade_relevance_v1.txt` (lenient) and `_v2.txt` (strict), `prompts/check_grounded_v1.txt`, the r_max and batching mode in `config.yaml`; each change is a new experiment.
- **Monitoring and feedback:**
  - Alerts: zero-context rate above the dev baseline; the only-gold-dropped count above 0 on regression items; parse failures above 2%; attempts at the cap above 10%; `finish_reason = length` on graders.
  - Dropped gold chunks become M5 items ("grader false reject") and T2 regression items.
- **Lifecycle:**
  - Analyze (`error-analysis` on dropped chunks and failed checks).
  - Measure (`code-based-evaluators`, `rag-evaluation`; grader quality via `judge-validation`, in V4).
  - Improve (prompt strictness, batching).
  - CI: a T1 graph test with a fake grader that must terminate; T2 abstention and false-abstention.
  - Monitoring (`ci-cd-evals`, `improving-llm-agents` for the cost cascade).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Grader LLM (default) | Groq `openai/gpt-oss-20b`, `reasoning_effort=low` | `GROQ_MODEL_ID` | — | no | 55–220 calls/run ≈ $0.007–0.014 | — | yes. No logprobs; tool calling yes; strict json_schema UNVERIFIED [59] |
| Grader LLM (when credits exist) | Claude Haiku 5.5 `claude-haiku-5-5`, effort `low` | — | — | no | ≈ $0.010–0.021/run | — | yes; a different family from the generator (bias control); structured outputs supported [63] |
| Groundedness check (local) | NLI cross-encoder or HHEM (V1 decision 1) | HF model | no | yes | 0 | Apache-2.0 (snippet) | yes |
| Relevance baseline (local) | `cross-encoder/ms-marco-MiniLM-L-6-v2` (R3) | HF model | via R3 | yes | 0 | Apache-2.0 (R3) | yes |
| Schemas | `pydantic`, `jsonschema` | 2.13.5 / 4.26.0 | yes (lock) | yes | 0 | MIT | yes |
| Graph | `langgraph` | 1.2.12 | no | yes | — | MIT | yes (LLMOps only) |
| Framework core | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes, through the adapter |
| Not installed | `langchain-groq` 1.1.3 | — | no | — | — | MIT | conflicts with `groq` 1.7.0 (foundation) |
| Read-only | `ragas` 0.4.3, `trulens` 2.14.0, `nemoguardrails` 0.24.1, `guardrails-ai` 0.11.0, `lettucedetect` 0.2.3 | — | no | — | — | Apache / MIT | **no**: pull openai, heavy, or a `python-dotenv==1.0.1` conflict |
| Tracing | JSONL + `arize-phoenix-otel`; `langsmith` | 0.17.2 / 0.14.4 | no | yes / SDK | — | Apache-2.0 / MIT | yes |

```text
uv add --group llmops langgraph==1.2.12 langgraph-checkpoint-sqlite==3.1.1   # from the foundation
```

Keys: `GROQ_API_KEY`; `ANTHROPIC_API_KEY` for the Haiku grader arm; `LANGSMITH_API_KEY` optional.

### 11. Open questions for Yash (preferences only)
- Gold relevance cut-off on the UMBRELA scale: **≥ 2** (recommended) or **≥ 1**?
- Show the strict and the lenient grader prompts side by side as two arms: **yes** (recommended) or one prompt only?

---

## Concept V3: Answerability and abstention (E, project v5.0)

### 1. Sources checked

**Book pages (cited from 02/03/04; UNVERIFIED here)**
- Ch3 p.7/14: handling ungrounded answers.
- Ch3 p.11/14: "I don't know" is preferable when wrong answers are costly. This is the only statement; there is no algorithm (04 notes it is p.11/14, not p.12/14).
- Ch22 p.11–12/19: robustness to noise (02).
- Ch22 p.13/19: test questions with no answer (03 §5 V3 row).
- Ch20 p.1/11: scores can look reasonable when nothing relevant was found (via C4 D.5).
- There is no dedicated book treatment (02: gap).

**Repo notebooks and cells (cited from 02/04; UNVERIFIED here)**
- `evaluation/evaluation_grouse.ipynb` cells 13–23: 02 calls these "positive acceptance / negative rejection" metrics; 04's Ch22 table maps the same cells to answer relevance (see V3-E3).
- `adaptive_retrieval.ipynb` cell 23: the prompt allows "don't know".
- `local_rag_huggingface_faiss.ipynb` cells 22 and 26: a refusal instruction; an out-of-scope probe with no saved output.
- `crag.ipynb` cell 26 and `self_rag.ipynb` cell 20: single out-of-domain demo queries with no metric.

**Existing course files read**
- 02 V3 card, Gate 3→4 and Gate 8→9; 03 stage 15 and the V3 row ("low top-1 score means unanswerable" listed as confused).
- 04 V3 row; 06 §3.3 (the fixed sentence), §6.2 (unanswerable target ≥ 8: 4 tempting, 2 false-premise, 2 out-of-domain), §6.7 seeds D-009 and D-010, §7.4 (abstention P/R/F1, false-abstention rate; the toy 0.636/0.700/0.667/0.08), §8.4 (≥ 15 rule; 6/6 → 0.54).
- 08 D-09, D-10.
- C4 D.5 (D-010 at 0.5196; scores are not probabilities and not comparable across models; the D-009 score 0.3099); C5 D.6 (`abstained` only for the exact sentence; a paraphrased refusal gets `no_citation`, T15); P7 D.7.
- The external review rows: Kalai item, phrase-list item, risk–coverage curve; Phase 3 research (M1 unanswerable kinds; CRAG scoring idea kept for V3).
- The misconception log (MC-006); `contracts_check.py` (`clopper_pearson_lower`, `wilson`).

**AE book sections:** none specific; the AE "context swap" probe belongs to P7 (external review). Not checked here.

**Interview-repo items (via the external review, UNVERIFIED here):**
- AIQ 02 Q50 (why models rarely say "I don't know");
- AIQ 04 Q60 (risk–coverage);
- AIQ 07 Q44 (vague answers inflate faithfulness);
- SDG `13-reliability-and-safety/01-guardrails.md`, 'Abstention Strategy'.

**External sources:**
- Papers, through their repos or scorers: [32] Sufficient Context; [34] AbstentionBench; [35] RGB; [36] Meta CRAG benchmark; [37] the SQuAD 2.0 scorer; [45] OR-Bench.
- Docs: [44] Cohere rerank best practices (verified); [14] Anthropic reduce-hallucinations guide (verified).
- Snippet only: [33] Wen et al.; [38] Kalai et al.; [39][40] Geifman et al.; [41] Yadkori et al.; [42] Kadavath et al.; [43] Kamath et al.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **Answerable is corpus-relative** (D-009 is "known" but not in the PDF) | the definition | Codex review note; 06 §6.7 | M1 / V3 | No | **core** | One sentence plus D-009: "answerable from these documents". |
| 2 | **Three unanswerable kinds**: tempting, false-premise, out-of-domain (+ ambiguity is different) | dataset and slices | Phase 3 M1 gap 9 (missing) | M1 | No | bridge | False premise is the hardest (AbstentionBench 0.551 mean recall, derived [34]); out-of-domain is easy, so keep it few. |
| 3 | **Ambiguity is not unanswerability** | scoring | external review §7 row 7 (no owner) | M1 / V3 | No | core | State the policy: an ambiguous item is scored on either reading, never as an abstention target (decision in 08 pending). |
| 4 | **Abstention P/R/F1, false-abstention rate** (positive = should abstain) | metrics | 06 §7.4; M3 (exposed) | M3 | exposed | bridge | Re-derive the 06 toy in two lines. |
| 5 | **Detecting an abstention**: exact string vs paraphrase vs hedge + answer | metric input | C5 D.6 (exact only) | C5 / V3 | No | **core** | A three-way label. Exact match first, then a small phrase list, then a manual review queue. Report all three counts (RGB undercount [35]). |
| 6 | **Scores are not probabilities and not comparable across queries or models** | the threshold policy | C4 D.5; MC-006 | C4 | No | bridge | Show the 10 seed scores on one axis (D-010 among the answerables). |
| 7 | **Threshold policies**: retrieval score, grader verdict, sufficiency, combined | the design | missing | V3 | — | **core** | Four policies, one table: what each sees, what it misses. |
| 8 | **Sufficient context** vs relevant context | grader design | missing | V3 | — | **core** | Joren's definition [32]: could a careful reader answer from these snippets alone? |
| 9 | **Dev/test discipline for the threshold** | calibration | 06 §9.4; M4 | M4 | No | bridge | Choose on dev, confirm once on test. The SQuAD scorer's `best_thresh` is fit on the scored file, an oracle [37]. |
| 10 | **Small-sample intervals**: exact (Clopper–Pearson) and Wilson | every claim | 06 §8.4 states the rule; no lesson | M3 / M4 | No | bridge | The table in §5. Say "two-sided" with 0.54; the one-sided bound is 0.607 (derived). |
| 11 | **Risk–coverage curve** | reporting | external review (optional) | V3 | — | core (Short: picture; Full: AURC) | Sweep the threshold; plot error rate among answered vs share answered. |
| 12 | **The cost of abstaining**: coverage loss on answerable items | the trade-off | 06 v5.0 tolerance | V3 | — | core | Report false abstention beside every recall number. |
| 13 | **Why models rarely say "I don't know"** (0/1 grading rewards guessing) | motivation | external review item | V3 | — | core (2 lines) | Kalai et al. [38]; CRAG's +1/0/−1 is the confidence-target-0.5 case [36]. |
| 14 | **Empty retrieval or filter output ≠ correct abstention** | metric hygiene | external review (R2, X3 items) | X3 / V3 | No | bridge | Separate reason codes: `policy`, `no_context`, `filter_empty`, `model_refusal`. |
| 15 | **Reasoning models abstain less** | model choice | missing | V3 | — | Full | AbstentionBench [34]; a hypothesis for gpt-oss-20b, tested by the abstention lab. |
| 16 | **Vague answers inflate faithfulness** | interplay with V2 | external review (AIQ 07 Q44) | V3 | — | Full | A hedge with no claims is "faithful". Count hedges separately. |

### 3. Quiz coverage

There is no `study/questions/V3_questions.md`. The questions it needs (titles only):
- **R-01** Define abstention precision, recall and the false-abstention rate; which is the positive class?
- **R-02** Why can't v0 abstain with "top score below 0.5"? (C4's CR-17 item.)
- **R-03** Name the three unanswerable kinds and which is hardest.
- **A-01** Compute P, R, F1 and false abstention from a 50 + 10 table (06 toy), then the exact 95% interval for 7/10.
- **A-02** Given 10 seed scores, sweep three thresholds and fill the risk–coverage table.
- **A-03** Label 6 replies: exact refusal, paraphrased refusal, hedge plus answer, answer.
- **T-01** A customer-support bot where a wrong answer costs 4× a refusal: what confidence target, and what score rule, follows?
- **T-02** (external review) Phrase list vs exact sentence: which error does each make?
- **Interview:** "With only 8 unanswerable questions, how would you choose and defend a refusal threshold?"

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| V3-E1 | 06 §6.2 (≥ 8 unanswerable) vs 06 §8.4 / Gate 8→9 (≥ 15, ≥ 5 in dev, before any threshold claim) | The dataset plan cannot reach the gate's own condition. Gate 8→9 then fails by design. | Raise the 06 §6.2 target to ≥ 15 (≥ 5 dev), or mark Gate 8→9's threshold part as "exploratory" until then (decision 2). |
| V3-E2 | 06 §3.3 design note "abstention machine-detectable" | Exact match misses paraphrased refusals, about 2× in RGB [35]. C5 already flags paraphrases as `no_citation`, so they currently count as *answers*. | Add a `refusal_paraphrase` label and report it apart from answers and exact abstentions. |
| V3-E3 | 02 V3 card vs 04 Ch22 table, row 4 | Both cite `evaluation_grouse.ipynb` cells 13–23, for different contents (negative-rejection metrics vs answer relevance). Not checkable here. | Re-open the notebook and fix one of the two. |
| V3-E4 | 06 §8.4 and 02 V3 "6/6 … lower bound ≈ 0.54" | Correct as the **two-sided** exact 95% bound; the one-sided bound is 0.607 (derived). | Say "two-sided". |
| V3-E5 | 02 V3 Book list | Lacks Ch22 p.13/19, which 03 cites for testing no-answer questions. | Add it (after checking the page). |
| V3-E6 | 02 V3 "Ext: none specific" | Sufficient Context, AbstentionBench, RGB, the CRAG benchmark and Kalai et al. are directly on topic. | Add Source C rows after verification. |

### 5. What the research says

**Sufficient Context** [32] (Joren et al., ICLR 2025; repo README verified, paper not opened)
- **The study:** a "sufficient context" label (could the question be answered from the snippets alone).
- **Autorater results:**
  - Gemini 1.5 Pro, 1-shot with chain of thought: accuracy 0.930 on 115 human-labelled items.
  - TRUE-NLI (T5-11B): 0.826.
  - "Contains the gold string": 0.809.
- **Model behaviour:**
  - With sufficient context, GPT-4o was 83% correct, 13% hallucinated and 4% abstained.
  - With insufficient context, hallucination rose to 15–40%, while answers were still correct up to about 35% of the time.
- **Selective generation:** a small logistic model combining self-rated confidence with the sufficiency label raised selective accuracy by 2–10 points at equal coverage.
- **Limits:** 115 validation items; a strong proprietary rater; the selective model is trained per dataset.
- **For the project:** a sufficiency verdict is the right *kind* of grader for tempting items. It is not a correctness oracle, so it is one input to the policy, measured on Yash's labels.

**AbstentionBench** [34] (repo and results CSV verified; the paper's "about 24%" is snippet only)
- **The study:** 20 datasets, 6 scenarios, 20 models.
- **Derived from the CSV** (mean abstention recall):
  - Llama 3.3 70B 0.668 vs its R1-distilled reasoning variant 0.475;
  - Qwen2.5 32B 0.731 vs s1.1 32B 0.441;
  - by scenario: false premise 0.551, underspecified context 0.564, answer unknown 0.784.
- **Abstention detection:** the repo offers both a keyword detector and a human-validated LLM judge.
- **Limits:** not RAG-specific; gpt-oss not tested.
- **For the project:** expect false-premise items to be missed most. Test, do not assume, how the default reasoning model behaves.

**RGB** [35] (code verified; numbers snippet only)
- The negative-rejection test feeds only documents without the answer and asks for a fixed sentence, as v0 does.
- Exact-substring rejection rate vs LLM-judged rejection rate: 24.67% vs 45.00% for ChatGPT (English).
- **For the project:** half of real refusals may be paraphrased. Measure both counts.

**Meta CRAG benchmark** [36] (code verified)
- Labels: perfect, acceptable, missing, incorrect. Scoring: correct +1, missing 0, incorrect −1. In code, score = (2·correct + missing)/n − 1 = (correct − hallucinated)/n.
- "Missing" is detected by the substring "i don't know".
- **For the project:** report this "truthfulness score" beside accuracy; it rewards abstaining only when the answer would be wrong.

**SQuAD 2.0** [37] (official scorer verified)
- Predict no-answer when `na_prob > thresh`.
- `find_best_thresh` picks the threshold on the same file it scores, so `best_f1` is an oracle upper bound.
- **For the project:** the textbook example of tuning on test. The course's dev/test rule is the fix.

**Kalai et al. 2025** [38] (snippet only)
- Under 0/1 grading, guessing never loses, so models learn to bluff.
- Proposed fix: state a confidence target t; a wrong answer costs t/(1−t) (t = 0.5 → 1; t = 0.9 → 9).
- **For the project:** the abstention policy must state its cost ratio; CRAG's score is t = 0.5.

**Selective prediction** [39][40][41][42][43] (snippet only)
- Risk–coverage curves and thresholds with guarantees (Geifman and El-Yaniv 2017). AURC is usually credited to Geifman, Uziel and El-Yaniv 2019.
- Conformal abstention (Yadkori et al. 2024): a guarantee only with exchangeable calibration data much larger than 15 items.
- P(IK) (Kadavath et al. 2022): reacts to added context; weak calibration on new tasks.
- A trained calibrator beats MaxProb under domain shift (Kamath et al. 2020: 56.1% vs 48.2% answered at 80% accuracy).
- **For the project:** with n ≈ 50 the curve is descriptive only; no guarantee is possible. A learned calibrator is out of scope; a hand-set rule on two signals is not.

**Cohere rerank best practices** [44] (docs source verified)
- `relevance_score` is in [0, 1] but depends on the query and is for ranking.
- Threshold recipe: 30–50 representative queries, each with a borderline document; the mean score is a reference threshold.
- **For the project:** more data than the dev split holds, so any reranker threshold is provisional.

**OR-Bench** [45] (README verified; numbers snippet only)
- Over-refusal on benign but scary-looking prompts trades off against safety.
- **For the project:** safety refusal is D4, not V3. Cite only to separate the two.

**Small-sample intervals (derived; hand-coded, cross-check with `contracts_check.py`)**

| n | correct | Exact (Clopper–Pearson) 95% | Wilson 95% |
|---|---|---|---|
| 6 | 6 | 0.541–1.000 | 0.610–1.000 |
| 6 | 5 | 0.359–0.996 | 0.436–0.970 |
| 8 | 8 | 0.631–1.000 | 0.676–1.000 |
| 10 | 8 | 0.444–0.975 | 0.490–0.943 |
| 15 | 15 | 0.782–1.000 | 0.796–1.000 |
| 15 | 13 | 0.595–0.983 | 0.621–0.963 |
| 20 | 18 | 0.683–0.988 | 0.699–0.972 |

- All-correct counts needed for the exact lower bound to reach a target: 0.5 → 6; 0.7 → 11; 0.8 → 17; 0.9 → 36.
- False abstention on 40 answerable items: 0/40 → 0–0.088; 2/40 → 0.006–0.169.

**Current practice (my interpretation).**
- Production RAG mostly uses prompt permission plus a fixed refusal or a refusal classifier, sometimes with a reranker floor.
- Evaluation uses exact strings or keyword lists plus an LLM check for paraphrases.
- Explicit cost-aware scoring (+1/0/−1) is spreading from benchmarks.

**Pitfalls (with evidence).**
- Tuning on test [37].
- String-only detection [35].
- Uncalibrated scores [44] (C4 D.5).
- Tempting items defeat score thresholds by design (D-010).
- False premise is the hardest kind [34].
- Reasoning models abstain less [34].
- Ambiguity mixed with unanswerability [32][34].
- Per-category thresholds at n = 4–10.
- An empty list scored as a correct abstention (no published source; a derived rule).
- A sufficiency verdict treated as truth [32].

**How to evaluate.**
- **Primary (deterministic):** abstention P, R and F1, with counts and exact intervals; false-abstention rate on answerables.
- **Also:** the CRAG-style score; the risk–coverage curve, exploratory at this size.
- **Slices:** by unanswerable kind and by reason code.
- **Retrieval metrics** only on answerables, and unchanged.
- **Baseline:** v0's prompt-only policy (its abstention metrics exist from v0.1).

**Interview questions**
1. Why not threshold the top-1 cosine?
2. How do you choose a threshold with 8 unanswerable items?
3. Precision or recall for abstention: who decides, and how?
4. Why do reasoning models abstain less?
5. How do you detect a refusal reliably?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. An abstention policy decides when the system should say "I cannot answer this from the provided documents" instead of answering.
2. A retrieval score cannot decide it alone: on our own data, an unanswerable question scored higher than five of eight answerable ones.
3. The stronger signal is whether the retrieved text is *sufficient* to answer, judged by the V2 grader. It is combined with the score and measured on labelled answerable and unanswerable questions.
4. We report how often we abstain when we should, how often we abstain when we should not, and the trade-off curve between them, with intervals, because we have very few unanswerable questions.
5. No threshold is claimed until we have at least 15 unanswerable questions, at least 5 of them in dev, and it is chosen on dev and confirmed once on test.

**The theory in one read (11 linked ideas)**
1. **Answerable from D:** a(q) = 1 if `evidence_groups` ≠ [] (06 §6.1).
2. **Abstention event:** A(q) ∈ {exact, paraphrase, hedge+answer, answer}; abstained = exact ∪ paraphrase (reported separately).
3. **Metrics:** P = |A ∧ ¬a| / |A|; R = |A ∧ ¬a| / |¬a|; F1; FAR = |A ∧ a| / |a|.
4. **Score policy:** abstain if s₁(q) < τ (top-1 retrieval or rerank score).
5. **Grader policy:** abstain if sufficient(q, context) = no.
6. **Combined policy:** abstain if (s₁ < τ) ∨ (sufficient = no), or a 2-signal table.
7. **Risk–coverage:** coverage(τ) = share answered; risk(τ) = error rate among answered.
8. **Truthfulness score:** (correct − hallucinated)/n; generalised penalty t/(1−t).
9. **Dev/test rule:** τ* = argmax on dev; one test evaluation.
10. **Intervals:** exact (Clopper–Pearson) for claims; Wilson for display.
11. **Reason codes:** policy, no_context, filter_empty, model_refusal.

**Formula sheet items:** P, R, F1, FAR; the CRAG score; t/(1−t); the Clopper–Pearson and Wilson formulas; "all-correct n for a target lower bound".

**Step-by-step outline (running example: the 10 Corpus D seeds, MiniLM v0 index, C4 D.3 table)**
1. Put the 10 rank-1 scores on one axis: answerables 0.2598–0.7094; D-009 0.3099, D-010 0.5196.
2. Sweep τ = 0.30, 0.43, 0.53 (derived from the table):
   - τ = 0.30: abstain on D-008 only → R = 0/2, FAR = 1/8.
   - τ = 0.43: abstain on D-008, D-004, D-005, D-009 → R = 1/2, FAR = 3/8.
   - τ = 0.53: abstain on everything except D-003, D-006 and D-007 → R = 2/2, FAR = 5/8.
3. Add a toy sufficiency grade (hand-made): D-010's chunks are about transport, so "insufficient". Shows the grader catching what the score cannot.
4. Classify 6 hand-written replies three ways; show how exact-only detection changes R.
5. Report with intervals: 2/2 has an exact lower bound of 0.158 (derived), which says almost nothing; hence the ≥ 15 rule.

**Visuals that earn their place**
- **Score strip of the 10 seeds** coloured by answerability: why no threshold separates them.
- **Risk–coverage curve** with dev and test points: the trade-off and the one-shot test.
- **Interval-width chart** (n = 6 … 40): why 15 is the minimum.

**Full only:** AURC; conformal abstention; P(IK); the Kalai argument in full; AbstentionBench scenario results; over-refusal as a D4 contrast.

### 7. Verify notebook plan

- **Recomputes:**
  - The 06 §7.4 abstention toy (0.636 / 0.700 / 0.667 / 0.08).
  - The 10-seed threshold sweep and risk–coverage table from the C4 D.3 scores. These are stored numbers: 0 API calls.
  - The interval table (cross-checked against `contracts_check.py`'s `clopper_pearson_lower` and `wilson`, and `scipy.stats.binomtest`).
  - The all-correct-n table.
  - The CRAG score on a toy table.
  - The three-way refusal classifier on 12 hand-written replies.
- **Plotly:** the interactive τ slider on the score strip and the risk–coverage curve.
- **Offline**; under 10 s.
- **No model calls.** The C4 scores are copied as data with their source (MiniLM fallback index; draft items; not an evaluation).

### 8. Apply-it tool plan and real-world checklist

`study/tools/abstention_curve.py`
- **Inputs:** a results JSONL (answers, abstention flags, top-1 scores, grader verdicts, `answerable`, `split`, unanswerable kind).
- **Outputs:**
  - per-policy P/R/F1/FAR with counts and exact intervals;
  - the risk–coverage curve (HTML);
  - the dev-chosen τ and its single test result;
  - slices by kind and reason code;
  - a three-way refusal table.
- **It refuses to print a "recommended threshold"** when the number of unanswerables in dev is below 5 or the total is below 15. It prints "exploratory" instead.

| # | Check | Auto / manual |
|---|---|---|
| 1 | At least 15 unanswerable items, at least 5 in dev, before any τ claim | auto |
| 2 | τ chosen on dev only; test touched once (logged) | auto |
| 3 | Abstention recall with an exact interval and counts | auto |
| 4 | False-abstention rate on answerables, with an interval | auto |
| 5 | Exact vs paraphrased refusals vs hedge-and-answer, counted separately | auto (phrase list) + manual review |
| 6 | Reason codes: empty retrieval or filter never counted as a policy success | auto |
| 7 | Results per unanswerable kind (tempting, false premise, out of domain) | auto |
| 8 | Ambiguous items excluded from abstention targets | auto |
| 9 | The score scale matches the index the threshold was set on (model id, normaliser) | auto |
| 10 | The CRAG-style score reported beside accuracy | auto |
| 11 | 5 abstentions and 5 answers on unanswerables re-read by you | manual |
| 12 | The cost ratio (t) is written down before choosing τ | manual |

**Recommendation logic.**
- Prefer the combined policy only if it beats the prompt-only baseline on dev F1 and its FAR stays within the pre-set tolerance.
- If the intervals overlap: "inconclusive; keep the simpler policy".

### 9. LLMOps notebook plan

- **Framework build.**
  - A small LangGraph branch on top of V2's graph: an `answerability_gate` node before `generate` reads s₁ and the sufficiency verdict, then routes to `abstain` or `generate`.
  - Without V2's graph, a plain function. A gate without a cycle does not need a graph (foundation §9.1).
- **Calls (cached):**
  - The score policy uses stored scores: 0 calls.
  - The sufficiency verdict reuses V2's batched grader with one extra field ("sufficient: yes/no"): 0 extra calls if added to V2's prompt, otherwise about 55 calls ≈ $0.007 on Groq (derived).
  - Generation runs only for questions the gate lets through; those are mostly cache hits from v4.x.
  - Replay-safe.
- **Tracing:**
  - The gate is an OpenInference `GUARDRAIL` span with inputs s₁, τ and the verdict, and output route plus reason code.
  - The root span gets `abstained`, `abstention_kind` (exact / paraphrase / hedge) and `reason`.
- **Dataset and evaluators:**
  - The golden set with `answerable`, the unanswerable kind and `split`.
  - Code evaluators: P/R/F1/FAR, the CRAG score, the risk–coverage AUC (descriptive), the refusal classifier.
  - Human review of paraphrase and hedge cases. No LLM judge (D-10).
- **Experiment:** v4.x champion (prompt-only abstention) vs score gate vs grader gate vs combined, on dev; the chosen arm once on test; the paired bootstrap on FAR and correctness.
- **Cost, latency, tokens:**
  - Abstaining saves the generation call. Report the calls saved per abstention and the net cost per question.
- **Versioning:** τ, the policy and the grader prompt version in `config.yaml`. A new τ is a new experiment, never a silent edit.
- **Monitoring and feedback:**
  - Alerts: abstention rate shifts by more than a set margin from the dev baseline (drift signal); paraphrased-refusal share above 10%; any `filter_empty` abstention.
  - Wrong answers on unanswerables become M5 items ("answered unanswerable") and new unanswerable items (new dataset version).
- **Lifecycle:**
  - Analyze (`error-analysis` of answered unanswerables).
  - Measure (`code-based-evaluators`).
  - Improve (τ, grader).
  - CI: the T2 abstention regression (foundation §12).
  - Monitoring (`ci-cd-evals`).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Intervals, binomial tests | `scipy` | 1.18.1 | yes (lock) | yes | 0 | BSD | yes; `binomtest(...).proportion_ci(method="exact"/"wilson")` |
| Reference implementations | `contracts_check.py` (course) | — | yes | yes | 0 | course | yes; cross-check target |
| Optional | `statsmodels` | 0.15.0 (2026-08-27) | no | yes | 0 | BSD-3 | optional; `proportion_confint`; adds patsy and formulaic |
| Sufficiency grader | Groq gpt-oss-20b (shared with V2) | `GROQ_MODEL_ID` | — | no | 0–55 calls/run | — | yes |
| Sufficiency grader (credits) | Claude Haiku 5.5 | — | — | no | ≈ $0.010/run | — | yes |
| Plots | `plotly` | lock | yes | yes | 0 | MIT | yes |
| Framework / tracing | `langgraph`, `langsmith`, `arize-phoenix-otel` | foundation pins | no | yes / SDK / yes | — | MIT / MIT / Apache-2.0 | yes (LLMOps only) |

No new install for V3.

### 11. Open questions for Yash (preferences only)
- Cost ratio for the policy: a wrong answer costs **1×** (CRAG, t = 0.5), **3×** (t = 0.75, recommended for a citation-checked assistant), or **9×** (t = 0.9) a refusal?
- Paraphrased refusals: count as **abstentions** in the headline (recommended, reported separately too) or as **format failures**?

---

## Concept V4: Hallucination-detection limits and judge reliability (U, project v5.0 validation)

### 1. Sources checked

**Book pages (cited from 02/04; UNVERIFIED here)**
- Ch22 p.7/19–p.8/19: claim decomposition and consistency sampling.
- Ch22 p.9/19–p.10/19: judge biases. The book's "15+ points" chain-of-thought claim is unmeasured (02 V4).
- Ch3 p.10/14–p.11/14: choosing verification models (04 V4 row).
- Ch22 p.11/19–p.12/19: the noise-ratio sweep, which 04 gives to "M4/V4". Phase 3 found it has no owner (M4-E1).

**Repo notebooks and cells (cited from 02/04/Phase 3; UNVERIFIED here)**
- `evaluation/evaluation_grouse.ipynb` cells 24–39: judge meta-evaluation against unit tests; answer order is fixed.
- `evaluation/end-2-end_rag_evaluation.ipynb` cells 12, 14 and 19: judges vs human labels. In cells 9 and 17 an LLM pre-filters its own benchmark. It uses external figshare data.
- `evaluation/open-rag-eval-example.ipynb` cells 11–12: a hallucination score. "HHEM" appears only in a saved log line (Phase 3 M3-E3).
- `reliable_rag.ipynb` cells 18 and 20: self-grading with the same model.

**Existing course files read**
- 02 V4 card and its two revision notes.
- 03 V4 row and the A4 ← V4 note.
- 04 V4 row and DV-13.
- 06 §8.2–8.6 (biases, mitigations, calibration rules, variance, the cost of the end batch).
- 08 D-10.
- External review §7 rows 12 (pass-keep lower bound), 14 (who labels), 15 (end-batch protocol), 16 and 17, and the V4 item "two LLMs agreeing".
- Phase 3 research gap 2: κ is not recommended for judges; judgy's interval holds p_obs fixed.
- `contracts_check.py`: `wilson`, `cohens_kappa`, `kappa_bootstrap`.
- Foundation §5: the judgy mapping.

**AE book sections (via the external review and Phase 3; UNVERIFIED here):**
- AE Ch4, NOTE in 'When to Use Other Metrics': κ is for human–human agreement; judge a judge on both error directions.
- AE Ch5, 'Estimating True Success Rates with Imperfect Judges' and 'Data Splits for Designing and Validating LLM-as-Judge'.

**Interview-repo items:** SDG `13-reliability-and-safety/02-ensemble-methods.md`, 'Panel of LLM Judges (PoLL)' (via the external review): two LLMs agreeing does not certify a judge.

**External sources:**
- Papers, through their repos: [46] SelfCheckGPT; [47] semantic entropy; [48] FActScore; [50] TRUE; [53] FairEval; [54] Judging the Judges; [56] Lee et al. reporting code; [57] FactCC.
- Source code: [58] statsmodels, scipy and judgy.
- Snippet only: [49] DnDScore; [51] Karbasi et al.; [52] Zheng et al.; [55] EvalGen. Also [17] RAGTruth and [5] LLM-AggreFact, shared with V1 and V2.

### 2. Gap audit

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **The detector is a classifier with its own error**: failure-catch rate and pass-keep rate | the whole concept | 06 §8.4; foundation §5 (vocabulary) | V4 (M3) | No (M3 exposed) | **core** | Teach the two plain names. AE's TNR is our failure-catch rate, and judgy's "TPR" is pass-keep (1 = Pass). |
| 2 | **Prevalence**: why accuracy and κ move with the class mix | reporting | missing | V4 | — | **core** | The derived 90%-agreement example below: κ = 0.39 with 4/10 failures caught. |
| 3 | **Confusion matrix as raw counts** | reporting | 06 §8.4 | M3 | exposed | bridge | Always print the 2×2 counts with labels on both axes. |
| 4 | **Wilson interval** for rates | failure-catch, pass-keep | 06 §8.4; `contracts_check.py` | M3 / M4 | No | bridge | Formula plus the table below. |
| 5 | **Cluster bootstrap over answers** | claims from one answer | 06 §8.4 | M4 | No | bridge | Resample whole answers; the derived example below is wider than Wilson. |
| 6 | **Cohen's κ, its variance, why not Wilson** | agreement | 06 §8.4; Phase 3 gap 2 | M3 | No | bridge | κ = (p_o − p_e)/(1 − p_e). statsmodels needs a table of **counts** and gives a symmetric Wald interval that can leave [−1, 1] [58]. Report κ; certify on the two rates. |
| 7 | **The certification rule** (lower bounds; the pass-keep addition) | decision | 06 §8.4; external review row 12 (proposed) | V4 / M3 | No | core | A failure class of n units certifies only with enough caught: 10 → 10/10, 30 → 26, 50 → 42 (derived). |
| 8 | **Challenge set**: fabricated claims, swapped citations, contradictions | enough failures | 06 §8.4 mentions it; no method | V4 | — | **core** | FactCC-style swaps with values from the same source [57]; label-preserving paraphrases as negative controls; built by code, then human-checked. |
| 9 | **Natural vs challenge failures** | reporting | 06 §8.4 ("report both") | V4 | — | core | κ and precision only on natural data; failure-catch per challenge class. |
| 10 | **Sampling-consistency checks** and their failure modes | Ch22 p.8/19 | Phase 3: "link only" from M3 | V4 | — | **core** (explain) | SelfCheckGPT and semantic entropy: they miss consistent errors, need temperature > 0 and cost N× [46][47]. In RAG, checking against the context is the better reference. |
| 11 | **Claim decomposition errors** | faithfulness metrics | Ch22 p.7–8/19; M3 | M3 | No | bridge | The split changes the verdict [49]; per-claim errors can cancel in a system score [48]. |
| 12 | **Judge biases**: position, verbosity, self-preference | the end-batch judge | 06 §8.2 | M3 | exposed | bridge | Recap in 3 lines; what each means for a groundedness check (verbosity → long answers "look" grounded). |
| 13 | **Corrected success rate** (Rogan–Gladen) and its instability | end batch | foundation §5; Phase 3 | V4 / D-10 | No | core (Full) | θ̂ = (p_obs + TNR − 1)/(TPR + TNR − 1); refuse to apply it when the denominator is below about 0.5 (derived table). |
| 14 | **No guarantee without failure labels** | why humans stay in the loop | missing | V4 | — | core (2 lines) | Karbasi et al. [51]; ties to "decide where a human spot-check is mandatory". |
| 15 | **Mandatory spot-checks**, and where | outcome 3 | missing | V4 | — | **core** | Numbers, dates and names; detector–human disagreements; borderline scores; a random slice of passes; the first batch after any model or prompt change. |
| 16 | **Re-certification triggers** | after D-10 | 06 §8.4 (model, prompt, generator, reasoning effort) | M3 / V4 | No | bridge | Add the retriever and the chunker: the inputs shift (Lee et al. [56]; EvalGen criteria drift [55]). |
| 17 | **Who labels the validation set** | certification | external review row 14 (proposed) | D-10 | — | bridge | Yash labels; Codex labels blind as a second opinion only. |
| 18 | **Noise-ratio robustness sweep** | Ch22 p.11–12/19 | no owner (Phase 3 M4-E1) | V4 or X | — | next | Optional V4 arm: fixed k, a varying share of gold chunks; random noise can help while distracting noise hurts (Phase 3 [S15]). |

### 3. Quiz coverage

There is no `study/questions/V4_questions.md`. The questions it needs (titles only):
- **R-01** Failure-catch rate vs pass-keep rate: define each, and map them to AE's TPR/TNR and to judgy's.
- **R-02** Why is a Wilson interval wrong for κ?
- **R-03** Two failure modes of sampling-consistency detectors.
- **A-01** From a 2×2 table (86, 4, 6, 4), compute agreement, κ, failure-catch and its Wilson interval.
- **A-02** How many of 30 failures must be caught to certify at a lower bound ≥ 0.70?
- **A-03** Build 4 challenge items from the D-001 gold sentence: number swap, page swap, negation, paraphrase (negative control).
- **T-01** (external review) "Codex and the Cohere judge agree on 95% of claims. Is the judge certified?"
- **T-02** Your detector was certified in March; in May you changed the chunker. What do you re-run, and why?
- **Interview:** "How do you know your hallucination detector works?"

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| V4-E1 | 06 §8.4 re-calibration triggers | Lists the judge model, the judge prompt, and the generator family and reasoning setting. It leaves out retriever, chunker and corpus changes, which shift the input distribution (Lee et al. [56]; EvalGen [55]). | Add "retriever, chunking or corpus version". |
| V4-E2 | Foundation §5 "judgy" row, and 06 §8.4 decision rule | judgy holds p_obs fixed, silently drops resamples where TPR + TNR ≤ 1, clips to [0, 1], uses unseeded global randomness and has no cluster option (source read [58]). Phase 3 noted the first point. | Reimplement it (about 60 lines) with Lee et al.'s interval, which resamples p_obs, TPR and TNR [56], plus a seed and a cluster option. |
| V4-E3 | 06 §8.4 κ via "statsmodels `cohens_kappa` as reference" | It needs a table of **counts** (it uses `table.sum()` as n), and its interval is symmetric Wald, which can leave [−1, 1]. A judge that always gives one label gives a NaN variance. | Note all three in the V4 lesson and the agreement report. |
| V4-E4 | 02 V4 card, "Ext: C#50, #51" | Neither ARES nor MT-Bench covers groundedness detectors. RAGTruth, LLM-AggreFact, TRUE and SelfCheckGPT are the on-topic primary sources. | Add Source C rows after verification. |
| V4-E5 | 04 Ch22 table row 8 and 02 M4/V4 | The noise-ratio sweep has no owner (also Phase 3 M4-E1). | Give it to V4 as an optional arm, or to X1/X3. |

### 5. What the research says

**SelfCheckGPT** [46] (Manakul et al., EMNLP 2023; README verified, paper not opened)
- **The study:** GPT-3 biographies (WikiBio), 238 passages labelled per sentence; extra samples at temperature 1.0.
- **The result (AUC-PR, NonFact):** random 72.96, BERTScore 81.96, NLI 92.50, Prompt (gpt-3.5-turbo) 93.42.
- **Its limits:**
  - About 73% of sentences are non-factual, so the baseline is high.
  - It assumes hallucinations vary between samples, so a fabrication repeated every time looks consistent.
  - It costs N samples per answer.
- **For the project:**
  - Explain it, and run it at most as a tiny demo (5 samples × 10 questions in `record` mode).
  - For RAG, the context is the better reference. The repo's own Prompt variant is a "supported by this passage?" check, which is what V1 already does.

**Semantic entropy** [47] (Farquhar et al., Nature 2024; code README verified, paper snippet only)
- Clusters sampled answers by meaning and takes the entropy across clusters. It targets confabulations (arbitrary, varying errors).
- It needs a GPU for large models, and consistently wrong answers pass.
- **For the project:** link only. Same family and same failure mode as SelfCheckGPT.

**FActScore** [48] (README verified) and **DnDScore** [49] (snippet only)
- FActScore splits text into atomic facts and checks each against Wikipedia.
- The automatic estimate is within about 2% of the human score at *system* level (snippet only). Per-claim errors can cancel out in that number.
- DnDScore: decomposition and decontextualisation pull against each other, and the order of the two steps changes the verdicts.
- **For the project:** certify per unit, not on an aggregate.

**Detector benchmarks** [5][17][50]
- LLM-AggreFact (snippet only): best checkers about 75–77% balanced accuracy on natural claims.
- RAGTruth (snippet only): prompted GPT-3.5 recall 92.3 but precision 37.1.
- TRUE (README verified): a fixed 0.5 cut-off may not suit a metric; thresholds must be tuned.
- **For the project:** expect a detector to be noticeably imperfect, and its two error directions to differ.

**Karbasi et al. 2025** [51] (snippet only)
- Automatic hallucination detection is impossible in general from correct examples alone. It becomes possible once examples labelled as wrong are given.
- **For the project:** the theoretical reason why labelled failures (the challenge set) are required.

**Judge reliability** [52][53][54][55]
- Zheng et al. 2023 (snippet only): GPT-4 agrees with humans over 80% on pairwise *preferences*; position, verbosity and self-preference biases. This does not transfer to groundedness detection.
- FairEval (repo verified): position bias with a mitigation. Snippet only: one model's win rate went from 2.5% to 82.5% by answer order.
- Judging the Judges (repo verified): high percent agreement can hide large score gaps, so use chance-corrected agreement. Later versions use Scott's π.
- EvalGen (snippet only): criteria drift; grading changes the grader's criteria.

**Reporting a judge-corrected rate** [56] (Lee et al., code verified)
- Implements the Rogan–Gladen estimator with an interval that includes uncertainty from the test p *and* the calibration rates, plus smoothing and calibration-budget allocation.
- **For the project:** use this, not judgy's interval, in the end batch.

**FactCC** [57] (README verified)
- Transformations: pronoun, date, number and entity swaps with values from the same source, negation, noise; back-translation as the label-preserving case.
- **For the project:** the recipe for the code-built challenge set.

**Derived numbers (numpy; formulas ported from scipy and statsmodels source)**

| Failure-catch | Point | Wilson 95% | Certifies (lower bound ≥ 0.70)? |
|---|---|---|---|
| 21/30 | 0.70 | 0.521–0.833 | no |
| 24/30 | 0.80 | 0.627–0.905 | no |
| 27/30 | 0.90 | 0.744–0.965 | yes |
| 8/10 | 0.80 | 0.490–0.943 | no |
| 10/10 | 1.00 | 0.722–1.000 | yes |

- Minimum caught for a lower bound ≥ 0.70: n = 10 → 10; 20 → 19; 30 → 26; 40 → 34; 50 → 42; 100 → 79.
- κ examples (n = 100; rows = human pass/fail, columns = detector pass/fail):
  - [[86, 4], [6, 4]]: 90% agreement, κ = 0.390 (Wald 0.086–0.694; paired bootstrap 0.060–0.679), failure-catch 4/10 (Wilson 0.17–0.69).
  - [[90, 0], [10, 0]]: 90% agreement, κ = 0, variance undefined.
  - [[45, 5], [5, 45]]: 90% agreement, κ = 0.80 (0.68–0.92).
- Rogan–Gladen instability, with p_obs moved 0.78 / 0.80 / 0.82:
  - denominator 0.85 → θ̂ 0.800 / 0.824 / 0.847;
  - denominator 0.20 → 0.40 / 0.50 / 0.60;
  - denominator 0.10 → −0.2 / 0.0 / 0.2.
- Cluster example: 25/30 claims from 10 answers, misses grouped. Wilson 0.664–0.927; the bootstrap over answers 0.60–1.00.

**Current practice (my interpretation).**
- Teams validate a judge or detector on a held-out human-labelled set, report both error directions, and re-validate after changes.
- They keep humans on disagreements and a random slice of passes.
- Small fine-tuned checkers (MiniCheck, Lynx, LettuceDetect) are often preferred to a prompted large model for cost.
- Anthropic's docs: code-based grading first, check an LLM grader's reliability before scaling it, rubric plus reasoning before the label (verified [14] and the eval docs).

**Pitfalls (with evidence).**
- Prevalence hides error (derived; SelfCheckGPT baseline [46]).
- Percent agreement is not alignment [54].
- Consistent hallucinations pass sampling checks [46][47].
- Self-consistency is the wrong reference in RAG.
- Decomposition changes verdicts [49].
- Judge biases [52][53].
- Criteria drift [55].
- A fixed 0.5 threshold [50].
- No guarantee without failure labels [51].
- A challenge set that is too easy: random swaps are obvious, so swap in-source values [57].

**How to evaluate.**
- On the natural human-labelled units (claims or sentences from v5.0 answers), report the 2×2 counts, failure-catch and pass-keep with Wilson or cluster intervals, and κ with the bootstrap.
- On the challenge set, report failure-catch per class (fabricated number, swapped citation, negation) plus pass-keep on the paraphrase controls.
- Apply the 06 §8.4 rule, plus the proposed pass-keep bound.
- For context only, compare against the NLI baseline and the LLM grader.

**Interview questions**
1. Why not report accuracy for a hallucination detector?
2. Why Wilson for rates but not for κ?
3. When does SelfCheckGPT fail?
4. Why is a judge-corrected rate unstable?
5. Where must a human still check?

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. A hallucination detector, whether a small model, an LLM grader or an LLM judge, is itself a classifier that makes mistakes, so its numbers mean nothing until we measure it.
2. We measure two rates against our own labels: how many real failures it catches, and how many good sentences it lets through. Each comes with an interval and its raw counts.
3. Because natural answers contain few failures, we add a challenge set built by code: swapped numbers, swapped citations and negated sentences.
4. Checks that sample the model several times and look for disagreement miss errors the model makes every time, cost several calls, and in RAG are weaker than checking against the retrieved text.
5. Humans stay on the cases detectors handle worst: numbers and names, disagreements, borderline scores, a random slice of passes, and the first run after any change.

**The theory in one read (12 linked ideas)**
1. **Units and labels:** claim or sentence u; human label h(u) ∈ {pass, fail}; detector d(u).
2. **Failure-catch rate** FC = |d = fail ∧ h = fail| / |h = fail|.
3. **Pass-keep rate** PK = |d = pass ∧ h = pass| / |h = pass|.
4. **Prevalence** π = |h = fail| / n, and why accuracy = π·FC + (1 − π)·PK moves with π.
5. **Wilson:** (p + z²/2n ± z√(p(1−p)/n + z²/4n²)) / (1 + z²/n).
6. **Cluster bootstrap:** resample answers, recompute FC.
7. **κ** = (p_o − p_e)/(1 − p_e); bootstrap interval; a report-only role.
8. **Certification:** LB(FC) ≥ 0.70 ∧ LB(κ) ≥ 0.40 (06), plus the proposed LB(PK) ≥ 0.70.
9. **Challenge transformations** (FactCC): number, date or entity swap from the same source; citation swap to an on-topic non-supporting block; negation; paraphrase as a control.
10. **Sampling consistency:** score = disagreement across N samples; blind to consistent errors.
11. **Corrected rate** θ̂ = (p_obs + FC − 1)/(PK + FC − 1), with "pass" as the success class; unstable when PK + FC − 1 is small.
12. **Spot-check policy:** the five triggers; re-certification triggers.

**Formula sheet items:** FC, PK, accuracy as a prevalence mix, Wilson, κ, θ̂, "minimum caught for LB ≥ 0.70".

**Step-by-step outline (running example: Corpus D gold sentences and v5.0 answers)**
1. Take the D-001 gold sentence (1.2 °C since the late 19th century, p.3) and build 4 items:
   - a number swap to 1.5 °C (a value from p.10/p.23, so plausible);
   - a citation swap to p.10;
   - a negation;
   - a paraphrase (control).
2. Run V1's checker on them by hand-made scores (in the lesson); show what it catches.
3. Fill a 2×2 table for 30 natural units and 30 challenge units; compute FC, PK and κ, with intervals.
4. Apply the rule: certify, or "human scoring continues".
5. Contrast with sampling consistency on D-009. If the model always says "1988", the samples agree and the check passes, yet the claim is not in the PDF.

**Visuals that earn their place**
- **2×2 confusion grid with prevalence slider:** how accuracy and κ move while FC and PK stay fixed.
- **Interval-width chart:** the minimum caught out of n for LB ≥ 0.70.
- **Challenge-set strip:** one source sentence and its four transformations, with which detector caught what.

**Full only:** semantic entropy; DnDScore; Rogan–Gladen and Lee et al.'s interval; Karbasi's impossibility result; the noise-ratio sweep; Scott's π vs Cohen's κ.

### 7. Verify notebook plan

- **Recomputes every derived number above:**
  - the Wilson table and the minimum-caught table;
  - the three κ tables, with the Wald and bootstrap intervals;
  - the Rogan–Gladen table;
  - the cluster example.
- **Cross-checks:** `contracts_check.py` (`wilson`, `cohens_kappa`, `kappa_bootstrap`), `scipy.stats.binomtest`, and `sklearn.metrics.cohen_kappa_score`.
- **Builds** the 4-item challenge strip for 3 gold sentences by code (regex number swap with in-source values, a page swap, negation templates).
- **Data:** the 06 §6.7 gold quotes; synthetic label tables.
- **No API calls.** Offline. Under 30 s, at 2,000 bootstrap draws.
- **Optional cell (off by default):** a SelfCheck-style demo reading 5 recorded samples for 3 questions from the cache. In `record` mode that is 15 Groq calls at temperature 1.0, once.

### 8. Apply-it tool plan and real-world checklist

`study/tools/judge_agreement.py`
- **Inputs:** a labels CSV (unit id, answer id, human label, detector label, optional score, source = natural or challenge, challenge class).
- **Outputs:**
  - the 2×2 counts;
  - FC and PK with Wilson and cluster-bootstrap intervals;
  - κ with the bootstrap;
  - per-class FC;
  - the certification verdict under the 06 rule and under the proposed rule;
  - a list of disagreements for review;
  - the "minimum caught" needed at the observed n.
- Offline; seeded.

| # | Check | Auto / manual |
|---|---|---|
| 1 | Raw 2×2 counts printed with the class names | auto |
| 2 | At least 30 failure units and at least 30 pass units, or the verdict is "too few" | auto |
| 3 | FC and PK with Wilson intervals; the cluster bootstrap when units share answers | auto |
| 4 | κ with the bootstrap (not Wilson); counts, not proportions, passed to statsmodels | auto |
| 5 | Natural and challenge results reported separately | auto |
| 6 | The challenge set uses in-source values and includes paraphrase controls | manual (inspect 10) |
| 7 | Labels frozen and hashed before the detector is run on them | auto (hash check) |
| 8 | The detector differs from the generator (model family or local model) | auto |
| 9 | Every disagreement reviewed by you | manual |
| 10 | A random 10% of detector passes re-read | manual |
| 11 | Re-certification flagged if the model, prompt, retriever, chunker or corpus hash changed | auto (compare config hashes) |
| 12 | The corrected rate refused when FC + PK − 1 < 0.5 | auto |

**Recommendation logic.**
- Certified → use the detector's numbers, with the human spot-check policy.
- Not certified, or too few units → report human labels only and name which class failed.
- PK low but FC high → the detector over-flags; use it as a triage queue, not as a gate.

### 9. LLMOps notebook plan

- **Framework build.**
  - No graph. An offline evaluation pipeline over stored traces: `load traces` → `units` (V1's sentence split) → `detectors` (local NLI, the V2 LLM grader from cache) → `join labels` → `agreement report`.
  - LangSmith: `evaluate(..., upload_results=False)` with summary evaluators for FC, PK and κ [61]. For Corpus D only, an annotation queue could hold Yash's labelling, but that is server-side and needs a key [61].
  - Phoenix stores annotations with annotator kind `HUMAN`, `LLM` or `CODE` [62].
- **Calls (cached):**
  - Running the V2 LLM grader on the challenge set: about 90 failure plus 30 control units ≈ 120 calls. Groq ≈ 120 × (1,000 × 0.075 + 100 × 0.30)/10⁶ ≈ $0.013; Haiku ≈ $0.018 (derived).
  - The local NLI: 0 calls.
  - The optional sampling demo: 15 calls.
  - The D-10 Cohere evaluation judge is **not** run here. Its certification uses this same tool in the end batch.
  - Replay-safe.
- **Tracing:**
  - Each detector verdict is an `EVALUATOR` span with unit id, model and revision, prompt version, score and label.
  - Human labels are stored as annotations with the labeller and the rubric version.
- **Dataset and evaluators:**
  - `detector_validation_v1.jsonl`: natural units from v5.0 dev traces plus the challenge set, frozen and hashed.
  - Disjoint from the rubric-tuning units (06 §8.4).
  - Code evaluators only.
- **Experiment:**
  - Local NLI vs HHEM (if both are allowed) vs LLM grader on identical units.
  - The primary readout is the certification verdict per detector; the secondary is cost and latency per unit.
- **Cost, latency, tokens:** per-unit p50/p95 latency (CPU for local, API for the LLM), cost per 1,000 units.
- **Versioning:** the detector id and revision, threshold, prompt version, label-file hash and challenge-generator version in the report header.
- **Monitoring and feedback:**
  - Online: the detector's flag rate per version (a shift beyond a set margin triggers a re-label sample); disagreement rate with the weekly human sample; config-hash changes trigger re-certification.
  - Missed failures found by humans become challenge items (new version).
- **Lifecycle:**
  - Analyze (`error-analysis` on disagreements).
  - Measure (`judge-validation`, `llm-as-judge` for the end batch).
  - Improve (threshold or detector choice).
  - CI: a T1 test of the statistics against `contracts_check.py`.
  - Monitoring (`ci-cd-evals`).
  - Labelling UI (`human-review-interfaces`; the study app or Phoenix).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Intervals | `scipy` | 1.18.1 | yes (lock) | yes | 0 | BSD | yes |
| κ | `scikit-learn` `cohen_kappa_score`; `contracts_check.py` | 1.9.1 | yes | yes | 0 | BSD | yes |
| κ variance (optional) | `statsmodels` | 0.15.0 | no | yes | 0 | BSD-3 | optional; mind counts vs proportions |
| Corrected rate (end batch) | `judgy` | 0.1.0 (2025-05-25) | no | yes | 0 | MIT | read; reimplement with Lee et al.'s interval [56] |
| Local detector | NLI cross-encoder / HHEM (V1) | HF model | no | yes | 0 | Apache-2.0 (snippet) | yes |
| LLM detector | V2 grader (Groq; Haiku with credits) | — | — | no | ≈ 120 calls ≈ $0.013–0.018 | — | yes |
| Sampling demo | `selfcheckgpt` | 0.1.7 (2024-03-10) | no | partly | — | MIT | **no**: pulls spacy, bert_score, openai; reimplement the Prompt variant in 20 lines |
| Labelling | study app (`study/app/`), or Phoenix annotations | — | yes / no | yes | 0 | — | yes |
| Tracing | JSONL, `arize-phoenix-otel`, `langsmith` | foundation pins | no | yes / SDK | — | — | yes |

No new install is required for V4. `statsmodels` is optional.

### 11. Open questions for Yash (preferences only)
- Adopt the external review's proposed pass-keep bound (LB ≥ 0.70) for detectors in Phase 8 too: **yes** (recommended) or **06 rule only**?
- Challenge-set size per class: **30** (recommended minimum) or **50**?

---

## Phase-level notes

**Order inside the phase.**
- V1 → V2 → V3 → V4 is right, and V4 must close the phase.
- V1's checker is reused by V2's output gate and V4's detectors.
- V2's batched grader carries V3's sufficiency field.
- V4 validates both V1's and V2's checkers on one shared label set.
- Building one shared `labels/` folder at the start avoids labelling the same units three times:
  - (question, chunk) relevance: about 220 pairs;
  - (sentence, citation) support: about 100;
  - natural answer units: about 60;
  - the challenge set: about 120.

**Labelling budget (derived; assumes about 20–30 s per pair and about 1 minute per answer).** About 500 units, roughly 4–5 hours of Yash's time. This is the real cost of Phase 8, larger than its API cost (under $0.10 per full set of runs on Groq).

**One definitions fix that several phases share.** "Supported" must mean the same thing in:
- 06 §7.4 citation metrics;
- V1's checker;
- V2's groundedness gate;
- the D-10 end-batch judge prompt (06 §8.3 `judge_faithfulness_v1`).

Recommendation: ALCE's joint-support rule, the sentence as the unit in v5.0, and the premise = the blocks the label resolved to. If the end-batch judge uses a different unit, its scores cannot be compared with V1's.

**Cross-phase effects.**
- **Phase 3 (M1):** needs at least 15 unanswerables (at least 5 in dev) before v5.0; tag each unanswerable kind; settle the ambiguity policy (external review row 7).
- **Phase 3 (M3):** the structured-output lesson (D-22) must exist before V2.
- **Phase 7 (X3):** the label scheme for merged windows decides V1's premise. Phase 7 suggests splitting by page.
- **Phase 9 (D1/D2):** the per-chunk grading arm's token use (about 180K per run) needs the rate limiter and resumable runs. The GUARDRAIL and EVALUATOR span kinds join the trace schema.
- **Phase 10 (A2, A3):** CRAG and Self-RAG reuse V2's grader and V3's policy. Their thresholds inherit MC-006. The recursion-limit default (10,007) affects every A-phase graph.
- **End batch (D-10):** V4's tool and challenge-set protocol are what certify the Cohere judge. Phase 8 builds the tool; the end batch uses it once.

**Default-model risk.** `gpt-oss-20b` is a reasoning model. Reasoning-tuned models abstained less in AbstentionBench, and NeMo's docs note reasoning models can run out of tokens before a verdict. Both are hypotheses for this model, to be measured in V3 (abstention by kind) and V2 (`finish_reason = length` on grader calls).

**Errors found that sit outside Phase 8's own files.**
- `uv.lock` pins `transformers` 5.19.0, uploaded 2026-10-06, newer than the 2-week rule as of this date. The compliant pin is 5.18.0. Report only; do not change the lock now.
- `LLMOPS_FOUNDATION.md` §6.2 lists the Sonnet 5.5 cache-read price as $0.20 per million tokens. The pricing page read today shows $0.10 [63].
- Foundation §9.2 and §9.3 should add:
  - the LangGraph recursion-limit default;
  - that `with_structured_output` on a custom chat model needs `bind_tools`;
  - the `tool_choice` "any" → "required" mapping for Groq (V2-E4).

---

## Sources

"Verified" means the page, repository file, source code or results file was opened in this session (2026-10-18). "Snippet only" means only a search-result summary was seen. Papers marked "repo verified" were checked through their official code repository, not the paper PDF. About 25 sources carry the research; the rest are library-source and documentation checks.

1. Gao, Yen, Yu, Chen. Enabling Large Language Models to Generate Text with Citations (ALCE). EMNLP 2023. https://github.com/princeton-nlp/ALCE (`eval.py`) — repo verified; paper https://arxiv.org/abs/2305.14627 snippet only.
2. Rashkin et al. Measuring Attribution in Natural Language Generation Models (AIS). Computational Linguistics 2023. https://arxiv.org/abs/2112.12870 — snippet only. Attributed-QA data: https://github.com/google-research-datasets/Attributed-QA — verified.
3. Liu, Zhang, Liang. Evaluating Verifiability in Generative Search Engines. Findings of EMNLP 2023. https://github.com/nelson-liu/evaluating-verifiability-in-generative-search-engines — repo verified; paper https://arxiv.org/abs/2304.09848 snippet only.
4. Li, Yue, Liao, Sun. AttributionBench: How Hard is Automatic Attribution Evaluation? Findings of ACL 2024. https://github.com/OSU-NLP-Group/AttributionBench — repo verified; numbers snippet only.
5. Tang, Laban, Durrett. MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents (LLM-AggreFact). EMNLP 2024. https://github.com/Liyan06/MiniCheck — README, source and benchmark notebook verified; paper numbers snippet only.
6. Godbole, Jia. Verify with Caution: The Pitfalls of Relying on Imperfect Factuality Metrics. Findings of ACL 2025. https://arxiv.org/abs/2501.14883 — snippet only.
7. Vectara. HHEM-2.1-Open, `vectara/hallucination_evaluation_model`; leaderboard https://github.com/vectara/hallucination-leaderboard — leaderboard README verified; model card snippet only.
8. sentence-transformers, pretrained cross-encoders (NLI). https://github.com/huggingface/sentence-transformers/blob/main/docs/cross_encoder/pretrained_models.md — verified.
9. Anthropic. Citations. https://platform.claude.com/docs/en/build-with-claude/citations — verified.
10. LangChain. How to get a RAG application to add citations (v0.3 docs). https://github.com/langchain-ai/langchain/blob/v0.3/docs/docs/how_to/qa_citations.ipynb — verified.
11. Turpin, Michael, Perez, Bowman. Language Models Don't Always Say What They Think. NeurIPS 2023. https://github.com/milesaturpin/cot-unfaithfulness — repo README verified.
12. Jacovi, Goldberg. Towards Faithfully Interpretable NLP Systems. ACL 2020. https://aclanthology.org/2020.acl-main.386 — snippet only.
13. Wallat, Heuss, de Rijke, Anand. Correctness is not Faithfulness in RAG Attributions. arXiv 2412.18004 (ICTIR 2025). https://arxiv.org/abs/2412.18004 — snippet only.
14. Anthropic. Reduce hallucinations. https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations — verified.
15. Yan et al. Corrective Retrieval Augmented Generation. 2024. https://github.com/HuskyInSalt/CRAG — code verified; paper https://arxiv.org/abs/2401.15884 snippet only.
16. Asai, Wu, Wang, Sil, Hajishirzi. Self-RAG. ICLR 2024. https://github.com/AkariAsai/self-rag — README verified.
17. Niu et al. RAGTruth. ACL 2024. https://github.com/ParticleMedia/RAGTruth — README verified; detector numbers snippet only.
18. Patronus AI. Lynx / HaluBench. arXiv 2407.08488. https://arxiv.org/abs/2407.08488 — snippet only (vendor).
19. Kovács, Recski. LettuceDetect. arXiv 2502.17125. https://github.com/KRLabsOrg/LettuceDetect — docs verified.
20. Thomas, Spielman, Craswell, Mitra. Large language models can accurately predict searcher preferences. SIGIR 2024. https://arxiv.org/abs/2309.10621 — snippet only.
21. Upadhyay et al. UMBRELA. 2024. https://github.com/castorini/umbrela — prompt verified; κ values UNVERIFIED.
22. LangGraph RAG examples: https://github.com/langchain-ai/langgraph/tree/main/examples/rag (`langgraph_self_rag.ipynb`, `langgraph_adaptive_rag.ipynb`, archived) and https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/agentic-rag.mdx — verified.
23. LangGraph 1.2.12, `langgraph/_internal/_config.py` (`DEFAULT_RECURSION_LIMIT`). https://pypi.org/project/langgraph/1.2.12/ — source verified.
24. ragas 0.4.3, `src/ragas/metrics/collections/faithfulness/` and `_faithfulness.py`. https://github.com/explodinggradients/ragas — source verified.
25. TruLens, `src/feedback/trulens/feedback/templates/rag.py`. https://github.com/truera/trulens — source verified.
26. NVIDIA NeMo Guardrails, fact-checking rail docs (`docs/configure-rails/guardrail-catalog/fact-checking.mdx`). https://github.com/NVIDIA/NeMo-Guardrails — verified.
27. Guardrails AI, provenance validators (README). https://github.com/guardrails-ai — verified (archived repos).
28. AWS. Bedrock Guardrails contextual grounding check. — snippet only.
29. Microsoft. Azure AI Content Safety groundedness detection. — snippet only.
30. Panickssery, Bowman, Feng. LLM Evaluators Recognize and Favor Their Own Generations. NeurIPS 2024. — snippet only.
31. Tang et al. Found in the Middle: permutation self-consistency for listwise ranking. NAACL 2024. — snippet only.
32. Joren, Zhang, Ferng, Juan, Taly, Rashtchian. Sufficient Context: A New Lens on Retrieval Augmented Generation Systems. ICLR 2025. https://github.com/hljoren/sufficientcontext — README verified; https://arxiv.org/abs/2411.06037 not opened.
33. Wen et al. Know Your Limits: A Survey of Abstention in Large Language Models. TACL 13 (2025), doi 10.1162/tacl_a_00754 — snippet only.
34. Kirichenko, Ibrahim, Chaudhuri, Bell. AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions. arXiv 2506.09038. https://github.com/facebookresearch/AbstentionBench — README and `analysis/abstention_performance.csv` verified; "about 24%" snippet only.
35. Chen, Lin, Han, Sun. Benchmarking Large Language Models in Retrieval-Augmented Generation (RGB). AAAI 2024. https://github.com/chen700564/RGB — code verified; numbers snippet only.
36. Meta. CRAG: Comprehensive RAG Benchmark (KDD Cup 2024). https://github.com/facebookresearch/CRAG — README and `local_evaluation.py` verified.
37. Rajpurkar, Jia, Liang. Know What You Don't Know: Unanswerable Questions for SQuAD. ACL 2018. Scorer: https://github.com/huggingface/evaluate/blob/main/metrics/squad_v2/compute_score.py — verified; paper snippet only.
38. Kalai, Nachum, Vempala, Zhang. Why Language Models Hallucinate. arXiv 2509.04664 (2025). — snippet only.
39. Geifman, El-Yaniv. Selective Classification for Deep Neural Networks. NeurIPS 2017. — snippet only.
40. Geifman, Uziel, El-Yaniv. Bias-Reduced Uncertainty Estimation for Deep Neural Classifiers (AURC). ICLR 2019, arXiv 1805.08206 — snippet only.
41. Abbasi-Yadkori, Kuzborskij et al. Mitigating LLM Hallucinations via Conformal Abstention. arXiv 2405.01563 (2024). — snippet only.
42. Kadavath et al. Language Models (Mostly) Know What They Know. arXiv 2207.05221 (2022). — snippet only.
43. Kamath, Jia, Liang. Selective Question Answering under Domain Shift. ACL 2020. — snippet only.
44. Cohere. Reranking best practices (`fern/pages/v2/text-embeddings/reranking/reranking-best-practices.mdx`). https://github.com/cohere-ai/cohere-developer-experience — verified (docs source, commit of 2026-10-16).
45. Cui et al. OR-Bench: An Over-Refusal Benchmark for LLMs. ICML 2025. https://github.com/justincui03/or-bench — README verified; numbers snippet only.
46. Manakul, Liusie, Gales. SelfCheckGPT. EMNLP 2023. https://github.com/potsawee/selfcheckgpt — README verified (results table); paper https://arxiv.org/abs/2303.08896 not opened.
47. Farquhar, Kossen, Kuhn, Gal. Detecting hallucinations in large language models using semantic entropy. Nature 2024, doi 10.1038/s41586-024-07421-0. https://github.com/jlko/semantic_uncertainty — README verified; paper snippet only.
48. Min et al. FActScore. EMNLP 2023. https://github.com/shmsw25/FActScore — README verified; estimator error snippet only.
49. Wanner, Van Durme, Dredze. DnDScore: Decontextualization and Decomposition for Factuality Verification. arXiv 2412.13175. — snippet only.
50. Honovich et al. TRUE: Re-evaluating Factual Consistency Evaluation. 2022. https://github.com/google-research/true — README verified.
51. Karbasi, Montasser, Sous, Velegkas. (Im)possibility of Automated Hallucination Detection in Large Language Models. arXiv 2504.17004 (2025). — snippet only.
52. Zheng et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023 (Source C #51). https://arxiv.org/abs/2306.05685 — snippet only.
53. Wang et al. Large Language Models are not Fair Evaluators. ACL 2024. https://github.com/i-Eval/FairEval — README verified; numbers snippet only.
54. Thakur et al. Judging the Judges. 2024. https://github.com/UMass-Meta-LLM-Eval/llm_eval — README verified; κ values snippet only.
55. Shankar et al. Who Validates the Validators? (EvalGen). UIST 2024. — snippet only.
56. Lee et al. How to Correctly Report LLM-as-a-Judge Evaluations. arXiv 2511.21140. https://github.com/UW-Madison-Lee-Lab/LLM-judge-reporting — code verified.
57. Kryściński, McCann, Xiong, Socher. Evaluating the Factual Consistency of Abstractive Text Summarization (FactCC). EMNLP 2020. https://github.com/salesforce/factCC — README verified.
58. Library source read: statsmodels `statsmodels/stats/inter_rater.py`; scipy `scipy/stats/_binomtest.py`; `judgy` 0.1.0 `core.py` (https://pypi.org/project/judgy/0.1.0/) — verified.
59. groq-python 1.7.0, `groq/resources/chat/completions.py` and `types/chat/completion_create_params.py`. https://pypi.org/project/groq/1.7.0/ — source verified (Groq's own docs pages blocked).
60. langchain-core 1.6.6 and 1.6.12, `langchain_core/language_models/chat_models.py` (`with_structured_output`). https://pypi.org/project/langchain-core/ — source verified.
61. langsmith 0.14.4, `langsmith/evaluation/_runner.py`, `evaluator.py`, `client.py`; docs `src/langsmith/local.mdx` and `annotation-queues.mdx` in https://github.com/langchain-ai/docs — verified.
62. arize-phoenix-evals 3.9.0 (wheel, `phoenix/evals/metrics/`) and openinference-semantic-conventions 0.1.41; spec https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md — verified.
63. Anthropic. Structured outputs, https://platform.claude.com/docs/en/build-with-claude/structured-outputs; Pricing, https://platform.claude.com/docs/en/about-claude/pricing; Models overview, https://platform.claude.com/docs/en/about-claude/models/overview — verified.
64. PyPI JSON API (https://pypi.org/pypi/<package>/json) for rapidfuzz, scipy, statsmodels, transformers, torch, sentence-transformers, judgy, lettucedetect, minicheck, selfcheckgpt, ragas, deepeval, trulens, arize-phoenix-evals, nemoguardrails, guardrails-ai, langchain-core, langgraph, langsmith, pysbd, nltk, syntok — verified.
65. langchain-groq (master), `ChatGroq.with_structured_output`. https://github.com/langchain-ai/langchain/tree/master/libs/partners/groq — source verified.
66. Course files read: `study/research/RESEARCH_PROMPT.md`, `LLMOPS_FOUNDATION.md`, `phase_03_measurement.md`, `phase_07_context_construction.md`; 01 (Source C, chapter rows); 02 (V1–V4 cards, Phase 8 table, §4 gates); 03 (stages 11 and 15, rows, notes); 04 (V1–V4 rows, Ch3, Ch19, Ch22 tables, §5, DV-08 to DV-13, DV-39, R-1); 06 (§2.5, §3.3–3.4, v5.0, §6.1–6.2, §6.7, §7.4–7.6, §8, §9.5); 08 Part 4 (D-01 to D-32); `concepts/C4_dense_retrieval.md`, `concepts/C5_generation_citations.md`, `concepts/P7_grounded_prompting.md`; `progress/concept_tracker.csv`, `progress/misconception_log.md`, `progress/session_log.md` (v0 facts line); `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md`; `sources/verification/corrections/contracts_check.py` (function list); `study/lessons/P3_bm25_gap_audit.md`; `study/FORMAT.md`; `pyproject.toml`; `uv.lock`.
