# P6 gap audit: how the lesson's contents were chosen

**What this is:** the check behind the P6 HTML lesson, so you can see why each part exists. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [P6_ir_metrics.html](P6_ir_metrics.html) (open it from the study kit: P6 → step 1). The full research is in `study/research/phase_01_prerequisites.md`, Concept P6.

## The method, in five steps

1. **Collect every idea the topic uses.** Sources:
   - the book pages (Ch22 p.4–8/19, p.13/19, p.18/19, and the glossary at App p.15/23 and p.18–20/23);
   - the old full lesson `concepts/P6_ir_metrics.md`, its lab and its 23 tests;
   - 06 §7.1–7.6 (the course's metric definitions) and §9.4 (how much 50 questions can detect);
   - the papers and tool documentation in the research (IIR §8.3–8.5, Järvelin & Kekäläinen 2002, Burges et al. 2005, TREC-8 QA, BEIR, the trec_eval source, ir-measures, RAGAS);
   - all 19 quiz questions.
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it (P2, P5, P6, M1, M2, M4, R3)? Your progress file says whether you have studied that concept. P2 is now written, but written is not studied, so P6 still carries a short bridge.
3. **Classify each idea.**
   - **Core:** taught in full.
   - **Bridge:** taught briefly, where it is needed.
   - **Next topic:** a link only.
4. **Check the quiz.** Every key point of every question must be taught in **Short**.
5. **Check the facts.**
   - Every number is matched against the measured facts file (`P6_FACTS.md`, S1–S11 and the new K1–K12).
   - Every book page is opened.
   - No run of 15 or more words is copied from the book.

## One change from the research blueprint: everything real is re-measured

The research's real-corpus numbers came from a scratch run. They were measured again by `p6_kit_measure.py` (K1–K12, byte-identical on rerun) on v0's **97 chunks**, the same chunks as P3, P4 and R1, with BM25 and the local MiniLM model. The scratch values were all reproduced, and the run added four things the blueprint did not have:
- **K9:** a real-corpus version of "unjudged = not relevant". Labels were kept only for the chunks one retriever put in its top 1 or 2. Precision@4 fell for both retrievers (0.3929 → 0.2500), and nDCG of the retriever whose pool made the labels went **up** (0.9839 → 1.0000), because missing labels shrink the ideal score too.
- **K11:** the same run scored by our code and by ir-measures (trec_eval underneath). The two agree to 1e-16 once ties and gains are aligned; a tie demo and a cut-off demo show what happens when they are not.
- **K12:** real seeds where MRR ties and nDCG does not (D-004, D-005).
- **K8:** the review item A-06's two AP values, now measured (0.5000 and 0.7500).

The graded step still uses the old toy (Q1, 0.5625), because the draft seeds have no grades.

## What step 2 found: the gaps in the old P6 files

The old lesson, code, tests and FACTS file agree with 06 §7.3. The gaps were things it never said.

| # | Idea | Before | Now in the lesson |
|---|---|---|---|
| 1 | **Relevance is a label, fixed before the run**, not a similarity score; a qrel is (question, chunk, grade) | assumed from P2 | step 2, a bridge with D-007's label row (Short) |
| 3 | **Unjudged = not relevant, and what it costs** (holes, pool bias) | the convention only | step 11 (Short): BEIR's measured holes plus K9 on the climate PDF |
| 4 | **k is what the language model receives**; candidate pool vs final top k | "always state k" | step 2 (Short); pool vs final in Full step 16, linked to R3 |
| 5 | **The Precision@k ceiling** n_rel / k | missing | step 4 (Short), with every seed at its ceiling (K5). Taught, never posed as a question |
| 7 | **"Recall" means four things** (IR Recall@k, hit rate or Success@k, ANN recall, RAGAS context recall) | missing | step 5 one line (Short); the full table in step 14 (Full) |
| 10 | **Where the nDCG formula comes from** (J&K 2002 vs Burges 2005 vs trec_eval) | history UNVERIFIED; 06 cites the wrong paper | step 7 one line (Short); step 15 table (Full) |
| 13 | **Retrieval quality vs answer quality**, and LLM-scored "context relevance" | Part E table | step 12 (Short), with the decision flow |
| 14 | **One number per question, then the mean, with n** | Full only | step 6 and step 12 (Short) |
| 15 | **Why small sets are noisy** (RR takes 11 values; ±0.12 at n = 50) | missing | step 12 one line (Short); step 16 (Full) |
| 16 | **CE@k vs Hit@k vs Recall@k on real questions** | toy preview | step 9 (Short): D-007 at k = 2 and D-005 at k = 1 |
| 18 | **Library conventions** (ties by docno, no RR cut-off, linear gain) | missing | step 13 one line (Short); step 15 (Full), measured in K11 |
| 22 | **The repo's answer-level "precision/recall"** (open-rag-eval cell 14) | missing | step 17 table (Full) |

Ideas that were already taught well stayed, rewritten in the house style:
- Hit@k, Precision@k (÷ k on short lists), Recall@k (÷ all relevant);
- RR and MRR, the cut-off and the 1 / mean-rank trap;
- DCG, IDCG from all relevant chunks, and the exp vs linear gain;
- what k does to each metric;
- MRR and nDCG disagreeing;
- AP's two denominators and context precision (Full).

## What step 4 found: the quiz against Short

All 19 questions are answerable from Short; `p6_md_check.py` checks that each one's reread line names the section that teaches it. The research had flagged three items whose key points were not in the old lesson's Short (R-05, A-05, T-03); steps 9, 11 and 5 now teach them.

| Questions | Taught in (Short) |
|---|---|
| PRE-01, R-01, A-01 | steps 3–5 |
| PRE-02, R-02, A-04 | step 6 |
| PRE-03, A-05 | step 9 |
| R-03, A-02 | step 7 |
| R-04, A-03 | step 10 |
| R-05 | step 11 |
| A-06 | step 4 (AP in one line), step 14 in Full |
| T-01 | steps 6, 12 |
| T-02 | step 12 |
| T-03 | step 5 |
| T-04 | step 13 |
| R-06 (interview, AIQ-04 Q43) | steps 5–7, 9, 12 |

The tutor-reserved interview question (AIQ-07 Q23) and the coach's hidden P6 seed and reserves are not used anywhere in the kit files. The Precision@k ceiling is taught but never asked.

## Left to other concepts on purpose (link only)

- **qrels, pooling and the labelling guideline in full:** P2 (step 2 is a bridge).
- **ANN recall and the tie rule's owner:** P5.
- **Span labels, the real CE@k, Group-Recall@k and Span-Coverage@k as reported metrics:** M2 (step 9 and Full step 16 preview them).
- **Writing the evaluation questions without leakage:** M1.
- **Bootstrap confidence intervals and significance tests:** M4.
- **Candidate pool vs final top k as an experiment:** R3.
- **LLM-judged context relevance and faithfulness:** run once at the end on stored traces (D-10), then C5 and M3.
