# P4 gap audit: how the lesson's contents were chosen

**What this is:** the check behind the P4 HTML lesson, so you can see why each part exists. Every idea the lesson needs had to be found and taught; none of it was optional.
**What this is not:** the lesson itself. That is [P4_embeddings.html](P4_embeddings.html) (open it from the study kit: P4 → step 1). The full research is in `study/research/phase_01_prerequisites.md`, Concept P4.

## The method, in five steps

1. **Collect every idea the topic uses.** Sources:
   - the book pages (Ch1 p.5–8/14, Ch6 p.1–2/14, Ch11 p.1/13, Ch12 p.8/14, Ch13 p.6–9/13, and the glossary at App p.13–16/23);
   - the old full lesson `concepts/P4_embeddings_similarity.md` and its lab;
   - the repo cells it cites;
   - Cohere's embed documentation (the project's default embedder);
   - all 21 quiz questions.
2. **For each idea, ask two questions.** Is it taught *before* it is used? Which concept owns it (P1, P2, P4, P5, P6, C3, R1, R3)? Your progress file says whether you have studied that concept.
3. **Classify each idea.**
   - **Core:** taught in full.
   - **Bridge:** taught briefly, where it is needed.
   - **Next topic:** a link only.
4. **Check the quiz.** Every key point of every question must be taught in **Short**.
5. **Check the facts.**
   - Every number is matched against the measured facts file (`P4_FACTS.md`, S1–S10 and the new K1–K13).
   - Every book page is opened.
   - No run of 15 or more words is copied from the book. The longest run the lesson shares with it is 7 words.

## One change from the research blueprint: the running example

The blueprint was written on the old 91 plain windows. The phase plan decided that every new retrieval example uses v0's **97 chunks**, the same chunks as P3 and R1. So the chunk-dependent numbers were measured again on the 97 chunks (`p4_kit_measure.py`, K1–K13, byte-identical on rerun):
- D-002's ranks;
- the wrong-model bug;
- vector lengths;
- token counts;
- the rerank;
- cut dimensions;
- int8 and binary.

Numbers that do not depend on chunking are reused from S2, S3, S5, S7, S9 and S10: the toy vectors, the sentence pairs, the DAC truncation passage and the prefix test. The old lab still uses the 91 windows, and the lesson says so.

## What step 2 found: the gaps in the old P4 files

| # | Idea | Before | Now in the lesson |
|---|---|---|---|
| 1 | **How an embedder learns**: contrastive pairs, the B × B batch matrix, the loss | not taught (a review note asked for it) | step 5 (Short: the card's facts and a measured toy batch; Full: InfoNCE, DPR) |
| 2 | **Pooling**: token vectors become one vector | not taught | step 2 (one line, Short); step 5 Full |
| 3 | **Encoder vs decoder**: why MiniLM cannot write answers | not taught (a review note asked for it) | step 5 (Short) |
| 4 | **Library score conventions**: FAISS squared L2, sentence-transformers' −L2, LangChain's 1 − d/√2 going negative | not taught; the old fix recommended the relevance helper | step 3 table and converter (Short); why the formula exists (Full) |
| 5 | **Cohere's settings**: `input_type`, `output_dimension`, `embedding_types`, `truncate`, 96 per call, unit length not documented | barely taught | steps 6, 7, 11 (Short); Cohere's 8,192 vs 128k marked UNVERIFIED (Full) |
| 6 | **Where an N × N matrix really appears**: training, dartboard, duplicate analysis | only "not in retrieval" | step 4 table (Short), so MC-002 has its true counterpart |
| 7 | **sentence-transformers' `encode_query` / `encode_document`** | missing (the lesson predated them) | step 7 (Short), measured identical for MiniLM |
| 8 | **Score scales and why no threshold transfers**, including a no-answer question that outscores answerable ones | numbers only | step 9 (Short); anisotropy and its limit (Full) |
| 9 | **Matryoshka and rescaling after a cut** | not taught | step 10 (Short: measured table; Full: chart and the paper) |
| 10 | **int8 and binary vectors** | not taught | step 10 (Short) |
| 11 | **Choosing a model**: MTEB to shortlist, your questions to decide; cost per call | not taught | step 11 (Short), with a cost and memory calculator |
| 12 | **Trained length vs served length** (128 vs 256) | only in 07 | step 6 (Short): 70 of 97 chunks are longer than 128 tokens |
| 13 | **Bridges**: top-k, rank, Hit@k, MRR (owned by P2 and P6, not yet studied) | used without definition | step 4, one sentence each |

Ideas that were already taught well stayed, rewritten in the house style:
- the three measures and the toy table;
- normalisation and L2² = 2 − 2cos;
- checking unit length;
- the wrong-model bug;
- truncation;
- the asymmetry problem and prefixes;
- bi- vs cross-encoder;
- negation blurring;
- the `graph_rag` inversion.

## What step 4 found: the quiz against Short

All 21 questions are answerable from Short; `p4_md_check.py` checks that each one's reread line names the section that teaches it. While writing the questions, the check caught one gap: P4-T-02's wrong answer relies on MMTEB's best public model being smaller than LLM-based embedders, which only Full had. One sentence was added to step 11 and to the reading file.

| Questions | Taught in (Short) |
|---|---|
| PRE-01, R-01, A-01 | step 2 |
| PRE-03, R-05, A-02, A-04 | steps 2–3 |
| PRE-02, R-02, R-06 | step 4 (R-06 also step 5) |
| R-07 | step 5 |
| A-03 | steps 1, 4 |
| A-05 | step 6 |
| R-04, R-08 (interview, AIQ-04 Q15) | step 7 |
| R-03 | step 8 |
| A-06, T-03 | step 10 |
| A-07, T-02 | step 11 |
| T-01 | steps 3, 5 |

The tutor-reserved interview question (AIQ-04 Q11) and the coach's hidden P4 seed are not used anywhere in the kit files.

## Left to other concepts on purpose (link only)

- **Exact and approximate vector search**, FAISS index types and the tie rule: P5.
- **Hit@k, MRR and the other metrics in full**, and the "recall" name table: P6.
- **Reranking as an experiment**, and late interaction: R3.
- **Hybrid search** for codes and exact terms: R1 (after P3).
- **The embedding cache key and building the index**: C3 (the lesson lists the fields in Full).
- **HyDE and document augmentation**, the asymmetry fixes: Q2 and I6.
- **The Cohere measurements**: the LLMOps notebook, once `study/llmops/` exists. Until then the lesson's Cohere column is empty, never guessed.
