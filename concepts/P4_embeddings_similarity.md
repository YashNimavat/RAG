# P4 — Embeddings and similarity: dot, cosine, L2, normalisation, bi- vs cross-encoders, asymmetry

> **What this file is.** The lesson for concept **P4** ([02 card](../02_RAG_MASTER_LEARNING_PLAN.md#p4)). It follows the Parts A–M template of [07](../07_SAMPLE_LESSON.md), at a smaller scale, like [P1](P1_llm_fundamentals.md).
> **How to use it.** Answers are hidden in collapsible blocks. Write your answer first, then open the block. Lines marked `> 🧭 Coach:` are instructions for the AI tutor; they add to [05 §3](../05_LEARNING_AND_RETENTION_SYSTEM.md#3-coaching-rules-for-the-ai-tutor) and cannot override it.
> **Labels.**
> - **UNVERIFIED**: not checked by running code or reading the primary source.
> - **Toy illustration**: numbers computed by code on made-up data, never a result about a real system.
> - **Illustration, not an evaluation**: a real model on two seed questions. It shows a mechanism; it is not a retrieval-quality result.
>
> Every number in this lesson comes from the local run of 2026-10-08 ([P4_FACTS.md](../sources/verification/P4/P4_FACTS.md), sections S1–S10 and S-src), from a logged earlier run (cited), from a derivation shown in the text, or carries a label. No Groq or Cohere call was made for this lesson.

## Lesson header

| Field | Value |
|---|---|
| Concept | **P4 Embeddings and similarity**: what an embedding is; dot product, cosine and L2 by hand; why L2 ranking equals cosine ranking for unit vectors; normalisation; the query is embedded with the same model; truncation (linked, not repeated); bi-encoder vs cross-encoder; query/document asymmetry (Cohere `input_type`, instruction prefixes). |
| Phase / tier | Phase 1, Prerequisites. Priority **E**. Fast track possible ([02 §5](../02_RAG_MASTER_LEARNING_PLAN.md#5-fast-track-rules-from-the-o1-diagnostic)). |
| Prerequisites | **P1** (tokens, `max_seq_length`), **P2** (query, document, ranking). |
| Comes next | **P5** exact k-NN in NumPy · **C3** embedding and indexing · **C4** dense retrieval and score inspection · **R-concepts** reranking (cross-encoders) · HyDE/HyPE (asymmetry). |
| Open misconception | **MC-002** "missing query-embedding step; similarity matrix" ([log](../progress/misconception_log.md)). This lesson is its remediation (with the P5 lab). O1 evidence: O1-Q02 (cosine formula not recalled, score 0), O1-Q10 (bi- vs cross-encoder not known, score 0), O1-TR1 (MC-002). |
| Time | A: 10 min · book block 1: 10 min · B–D: 45 min · E–G: 20 min · H (lab): 45 min · J–K: 15 min · L: 15 min · M: 5 min. May be split across two days. Part I does not apply. |
| Mastery (P4 → `applied`) | Without notes, you can: (1) compute dot, cosine and L2 for 3-d vectors; (2) show that L2² = 2 − 2cos for unit vectors, so the rankings agree; (3) say whether a given model outputs unit vectors, and how you checked; (4) state that the query goes through the **same** model; (5) explain bi- vs cross-encoder (what is precomputed, what is not); (6) explain asymmetry and `input_type`. Lab: `coding_independence_0_3 ≥ 2`. |
| Mastery (P4 → `transfer`) | You also pass a fresh novel-scenario item (L.3) and score `debugging_0_3 ≥ 2` in the lab. |
| 02 evidence to produce | Hand computations without notes (Part F, lab Tasks 1–4); a short write-up of the `graph_rag` inversion (H.2, lab wrap-up 2); the max sequence length of your chosen model **with its source** (lab wrap-up 1). |

### Source map

| Source | Where | What it contributes |
|---|---|---|
| Book (A) | Ch1 p.5/14, p.6/14, p.8/14; Ch12 p.8/14; Ch13 p.6/13, p.7/13, p.9/13; Ch6 p.1/14, p.2/14; Ch11 p.1/13; App p.13–16/23 | Embeddings as "meaning coordinates"; the query embedded the same way; cosine named late; bi- vs cross-encoder; the asymmetry problem. **No formula, no metric choice, no normalisation, no truncation.** |
| Repo (B) | `dartboard.ipynb` 23; `json_rag.ipynb` 19, 21–23; `local_rag_huggingface_faiss.ipynb` 10, 13, 14, 16; `graph_rag.ipynb` 12; `reranking.ipynb` 27, 29; `simple_csv_rag.ipynb` 12; `helper_functions.py` L48–L74 | Real metric choices to read and critique, including one inversion |
| Our logs | [`progress/O2_smoke_test_2026-10-08.json`](../progress/O2_smoke_test_2026-10-08.json) (`cohere_embed`); [P1 D.4](P1_llm_fundamentals.md#d4-embedding-truncation-what-minilm-actually-reads) | Cohere `input_type`; truncation |
| Lab verification | [`sources/verification/P4/`](../sources/verification/P4/): `p4_measure.py`, `p4_sources.py`, saved outputs, [`P4_FACTS.md`](../sources/verification/P4/P4_FACTS.md) | Every measured number here |
| Source C (external) | C#16–#21 in [01 §6](../01_SOURCE_INVENTORY.md#6-source-c--supplementary-references-external) (SBERT, DPR, MTEB); C#52 (Cohere input types) | Further reading only |

### Contents

[Part A](#part-a--prior-knowledge-recovery) · [Read in the book](#read-in-the-book) · [B](#part-b--why-p4-exists) · [C](#part-c--intuition-and-analogy) · [D](#part-d--technical-mechanism) · [E](#part-e--connections) · [F](#part-f--worked-example-by-hand) · [G](#part-g--source-connection) · [H](#part-h--implementation-progression) · [I](#part-i--controlled-experiment) · [J](#part-j--failure-and-debugging) · [K](#part-k--engineering-decisions) · [L](#part-l--assessment) · [M](#part-m--retention) · [References](#source-references) · [Verification log](#verification-log)

---

## Part A — Prior knowledge recovery

Answer the six questions **before** reading on: 1–3 sentences each, no notes. Wrong answers are useful; they tell the tutor where to start.

> 🧭 Coach: Ask **one item at a time** (CR-01), in the exact wording below, with its reply template. Record confidence 1–3 before revealing anything (CR-16). Score with the Recall rubric ([05 §4.2](../05_LEARNING_AND_RETENTION_SYSTEM.md#42-graded-rubrics-04)). These are unscheduled recall items: log them, do not change the schedule, except that a score ≤ 1 follows the ≤ 1 row of [05 §5.2](../05_LEARNING_AND_RETENTION_SYSTEM.md#52-spaced-repetition-schedule). Do not correct in detail yet; route with the table after P4-A6. O1 showed confident-and-wrong answers (mean 1.1/4 at confidence 3): say so if it happens again.

**P4-A1.** What is an embedding?

*Reply template:* "An embedding is ____. Two texts with similar meaning get ____."

<details><summary>What a strong answer contains</summary>

- A **fixed-length list of numbers** (a vector) that a trained model computes for a text: 384 numbers for MiniLM (S1).
- Similar meanings point in similar directions, so their similarity is high (0.5356 for the book's emissions/CO₂ pair vs −0.0859 for an unrelated pair, S5). Boundary: "have risen" vs "have not risen" scores 0.8436 (S5): close vectors, opposite claims.

</details>

**P4-A2.** Write the formula for cosine similarity.

*Reply template:* "cos(a, b) = ____ divided by ____."

<details><summary>What a strong answer contains</summary>

- cos(a, b) = (a · b) / (‖a‖ ‖b‖): the dot product divided by the product of the two lengths.
- Range −1 to 1. It measures the **angle** only; lengths cancel. For unit vectors it is just the dot product.
- ⚠️ O1-Q02 flag: the formula was not recalled at O1.

</details>

**P4-A3.** A user types a question. What happens to the question before the search?

*Reply template:* "The question is ____ by ____. Then each chunk gets ____."

<details><summary>What a strong answer contains</summary>

- The question is **embedded with the same model** that embedded the chunks (Ch1 p.8/14).
- Then **one score per chunk** is computed (query vs each chunk vector), and the top-k are kept. For 91 chunks that is a vector of 91 scores, not a 91 × 91 matrix (S6).
- ⚠️ MC-002 flag: "a similarity matrix" or no query-embedding step.

</details>

**P4-A4.** A vector store returns chunk X with score 0.3 and chunk Y with score 0.8. Which is closer to the query?

*Reply template:* "It depends on ____. If the score is ____, then ____ is closer."

<details><summary>What a strong answer contains</summary>

- It depends on **whether the score is a similarity or a distance**.
- Similarity (cosine, dot): higher = closer, so Y. Distance (L2): lower = closer, so X. Check the library's metric before using the number. The repo's FAISS indexes are all `IndexFlatL2` (S-src), so their scores are distances.

</details>

**P4-A5.** What is the difference between a bi-encoder and a cross-encoder?

*Reply template:* "A bi-encoder ____. A cross-encoder ____. The first is used for ____ and the second for ____."

<details><summary>What a strong answer contains</summary>

- **Bi-encoder:** query and document go through the model **separately**, one vector each; compare the vectors. Document vectors are computed once and stored. Used for first-stage search.
- **Cross-encoder:** query and document go in **together** as one input; out comes one relevance score. Nothing can be precomputed, so every pair costs a model pass. Used to rerank a short list.
- ⚠️ O1-Q10 flag: not known at O1.

</details>

**P4-A6.** Should a question and a chunk always be embedded in exactly the same way?

*Reply template:* "Same ____, but possibly a different ____, because ____."

<details><summary>What a strong answer contains</summary>

- Same **model** always. But some models expect a different **input type or prefix** for queries and documents (Cohere `input_type` = `search_query` vs `search_document`; some models' query instructions).
- Reason: questions are short and interrogative, chunks long and declarative (the book's asymmetry problem, Ch6 p.1/14); such models were trained with that distinction.
- Boundary: adding a prefix to a model **not** trained with one just changes the vector (D.8).

</details>

> 🧭 Coach: **Routing.**
>
> | Weak answers (score ≤ 1) | Action |
> |---|---|
> | P4-A1 | Teach Part C first, then D.1. |
> | P4-A2 or P4-A4 | Teach D.2–D.3 slowly with Part F on paper **before** any code. |
> | P4-A3 | MC-002 is live. Draw D.1's diagram with the learner; do lab Task 7 early. |
> | P4-A5 | Teach D.7; read Ch13 p.6–7/13 together. |
> | P4-A6 | Teach D.8 after D.7. |
> | All six ≥ 3 with confidence 3 | Offer the fast track: D.3, D.4, D.7, D.8, F, H and L (evidence is never skipped, 02 §5 rule 1). |

---

## Read in the book

> 📖 **Read these pages now (after Part A, never before), in this order.** Each takes 2–4 minutes. After each page, close the book and write one line from memory.
>
> | When | Pages | Look for |
> |---|---|---|
> | Now (block 1) | **Ch1 p.5/14 → p.6/14** (Step 4) | The "GPS coordinates for meaning" analogy and the emissions vs carbon-dioxide example. Notice: the book never says **how** "close" is measured. |
> | Now (block 1) | **Ch1 p.8/14** (Step 6) | The query is embedded by the same process as the chunks, so both live in one space. This is the MC-002 step. |
> | After D.6 (block 2) | **Ch13 p.6/13 → p.7/13** | Why the bi-encoder is fast (documents precomputed) and what it cannot see; why the cross-encoder is accurate but cannot precompute. Check the diagram on p.7. |
> | After D.6 (block 2) | **Ch13 p.9/13** | Cross-encoder rerankers are trained relevance scorers; their limit is that you cannot add custom criteria by prompting. |
> | After D.7 (block 3) | **Ch6 p.1/14 → p.2/14** | The asymmetry problem: a short question and a long answer can embed far apart. |
> | At Part M (check) | **Ch12 p.8/14**, then **App p.15/23** (Cosine Similarity) | Ch12 p.8 is the book's first use of the word cosine (bounded between −1 and 1). The glossary says Chapter 1 explains it. Does it? (DV-B4) |
>
> 🧭 Coach: one question after block 1 only: "In the book, how is the question turned into something the system can compare with chunks?" Expected: it is embedded with the same process as the chunks (Ch1 p.8/14).

---

## Part B — Why P4 exists

### B.1 Three silent errors, none of which raises an exception

1. **The wrong model for the query.** We embedded the D-002 question with a different 384-dimension model (`paraphrase-MiniLM-L3-v2`) and scored it against MiniLM-L6 chunk vectors. No error. The gold window fell from rank **2** to rank **19** of 91, and every score shrank to between −0.11 and 0.19 (S6).
2. **A distance used as a similarity.** `graph_rag.ipynb` cell 12 sets `priority = 1 / similarity_score` and pops the smallest priority first. If that score is an L2 distance (the LangChain FAISS default; UNVERIFIED locally), the **closest** node is explored **last** (S10).
3. **Truncation.** A chunk whose answer sits after token 254 scores exactly the same against the question as the chunk without it: cos **0.019276** both ways (S7; mechanism in [P1 D.4](P1_llm_fundamentals.md#d4-embedding-truncation-what-minilm-actually-reads)).

### B.2 What the book leaves out

The book's whole treatment of "closeness" is an analogy (Ch1 p.5–6/14). It names cosine only in Ch12 p.8/14 and the glossary. It never mentions dot product, Euclidean/L2 distance, unit vectors, normalisation, input types, prefixes or truncation (S-src absence checks). The repo uses all of these. P4 fills the gap.

---

## Part C — Intuition and analogy

**Each embedding is an arrow from the origin.** Picture each chunk as an arrow in space; similar texts get arrows that point the same way.

- **Cosine** looks only at the **angle** between two arrows. Same direction = 1; at right angles = 0; opposite = −1. Length does not matter.
- **Dot product** is angle **and** lengths together: cos × ‖a‖ × ‖b‖. A longer arrow gets a bigger dot product even at the same angle.
- **L2 distance** is the gap between the two arrow **tips**. A long arrow and a short arrow in the same direction are still far apart.

**Normalising** cuts every arrow to length 1. Then all tips sit on one sphere, and the gap between two tips depends only on the angle. That is why the three measures agree after normalisation (D.3).

**The book's GPS analogy** (Ch1 p.5/14) is a distance picture: nearby places, nearby meanings. **Where it breaks:** on a map, distance is the only measure. With embeddings, the arrow length often carries no meaning, so the angle is what you want.

> 🧭 Coach: CR-17. Stop and ask one question: "Two arrows point the same way, but one is twice as long. Is their cosine 1, or less than 1?" Expected: exactly 1; cosine ignores length.

---

## Part D — Technical mechanism

> 🧭 Coach: CR-17. Teach one subsection per turn, then ask its one question before moving on. D.1: "How many scores does one question produce against 91 chunks?" · D.2: "Which document does raw L2 rank first in the toy?" · D.3: "For unit vectors, L2 squared equals what?" · D.4: "How would you check that a model outputs unit vectors?" · D.5: "Same dimension, different model: will Python complain?" · D.6: "Can text after token 254 help a chunk get retrieved?" · D.7: "Which of the two encoders can store document vectors?" · D.8: "Which `input_type` do questions get in Cohere?"

### D.1 The objects involved (MC-002 fix)

```mermaid
flowchart LR
    subgraph Index time, once
      C["Chunks (91 windows)"] --> M1["Embedding model<br/>(e.g. MiniLM-L6)"] --> V["Matrix E<br/>91 × 384"]
    end
    subgraph Query time, every question
      Q["Question"] --> M2["The SAME model<br/>(query input type, if the model has one)"] --> q["Query vector q<br/>384"]
    end
    q --> S["Scores = E · q<br/>one number per chunk: shape (91,)"]
    V --> S
    S --> K["Top-k chunks"]
```

- **The question is embedded.** Same model, same space (Ch1 p.8/14; the repo says the same in `json_rag.ipynb` cell 22).
- **One query, one score per chunk.** A 1 × 91 vector of scores, not a "similarity matrix" (an all-pairs matrix would be 91 × 91 = 8,281 scores, S6). The only all-pairs matrix in this concept is dartboard's K × K candidate matrix, used for **diversity**, not retrieval (G.2).

### D.2 The three measures

For vectors a and b with n numbers each:

```text
dot(a, b)  = a1·b1 + a2·b2 + … + an·bn
‖a‖        = sqrt(dot(a, a))                     (the length)
cos(a, b)  = dot(a, b) / (‖a‖ · ‖b‖)              (similarity: higher = closer, range −1..1)
L2(a, b)   = ‖a − b‖ = sqrt(Σ (ai − bi)²)         (distance: lower = closer, range 0..∞)
```

**Toy illustration** (S2): q = [1, 2, 2] and three documents. You will redo this by hand in Part F.

| Doc | Vector | Length | dot | cos | L2 |
|---|---|---|---|---|---|
| d1 | [2, 1, 2] | 3 | 8 | 0.8889 | 1.4142 |
| d2 | [0, 3, 4] | 5 | 14 | 0.9333 | 2.4495 |
| d3 | [2, 4, 4] (= 2q) | 6 | 18 | 1.0000 | 3.0000 |

- **Cosine ranks d3, d2, d1.** d3 points exactly along q.
- **Raw L2 ranks d1, d2, d3: the exact reverse.** d1 is short like q, so its tip is near q's tip; d3 points the same way but is twice as long.
- **Dot agrees with cosine here by luck** of these lengths. In general it does not (D.4).

### D.3 Normalisation, and the proof that L2 then ranks like cosine

**Normalise:** â = a / ‖a‖, so ‖â‖ = 1. For unit vectors:

```text
‖â − b̂‖² = ‖â‖² + ‖b̂‖² − 2 â·b̂ = 1 + 1 − 2 cos(a, b) = 2 − 2 cos(a, b)
```

- So **L2² = 2 − 2cos**. As cosine goes up, L2 goes down, always. The orderings are mirror images: smallest L2 = largest cosine. **Same ranking.**
- Also **â · b̂ = cos(a, b)**. On unit vectors, dot, cosine and L2 all give the same ranking.
- Toy check (S2): unit-vector L2 = 0.4714, 0.3651, 0.0000, so the ranking is d3, d2, d1 (like cosine); and 0.4714² = 0.2222 = 2 − 2 × 0.8889.
- Numeric check, as 04 proposed (S3, toy random data, 1,000 docs × 100 queries × 384 dims): max |cos − dot of unit vectors| = 4.44e-16; max |L2² − (2 − 2cos)| = 1.78e-15; **100/100** queries had the identical full ranking.

### D.4 Does your model already output unit vectors? Check, do not assume

| Pipeline (91 climate windows, S4) | Vector lengths |
|---|---|
| `all-MiniLM-L6-v2`, default | 1.000000 to 1.000000 (it ends with a **Normalize** module, S1) |
| Same model with Normalize removed | 2.008 to 3.043 |
| `paraphrase-MiniLM-L3-v2`, default | 2.255 to 3.371 (**no** Normalize module) |

- **How to check:** list the model's modules, or compute `np.linalg.norm(E, axis=1)` (lab Task 5). `normalize_embeddings=True` on MiniLM-L6 changes nothing (max difference 2.98e-08, S4).
- **Does it matter on real data?** It depends on how much lengths vary.
  - Toy (S3): when document lengths varied 0.5–2×, raw-L2 top-1 differed from cosine top-1 for **94/100** queries, raw-dot for **68/100**.
  - Real (S6, illustration): on unnormalised MiniLM-L6 vectors (lengths 2.0–3.0), raw L2 changed only the **5th** place for D-002 (window 65 replaced 25). Small here; not guaranteed elsewhere.
- **So:** normalise once at index time and at query time, then use any of the three. This is what `local_rag_huggingface_faiss.ipynb` cell 14 does.

### D.5 Same model for the query, and what scores look like

- **Wrong model, no error (S6).** Query by L3, chunks by L6, both 384-d: D-002's gold rank 2 → **19**; D-004's 1 → 2. Scores collapse to near 0 (−0.11 to 0.19; right model up to 0.46–0.48). Dimension match is **not** a compatibility check. Store the model id with the index (C3).
- **Typical values (S5, MiniLM-L6).** Paraphrase pair 0.6918; book pair 0.5356; unrelated pairs −0.0859 and −0.0478; best chunk for a real question 0.46–0.48 (S6). A "good" cosine is model-specific. Never carry a threshold from one model to another.
- **Limit.** "Have risen" vs "have not risen": **0.8436** (S5). Embeddings capture topic far better than negation.

### D.6 Truncation (linked, not repeated)

The mechanism is in [P1 D.4](P1_llm_fundamentals.md#d4-embedding-truncation-what-minilm-actually-reads) and [07 D.6](../07_SAMPLE_LESSON.md#d6-embedding-truncation-the-hard-ceiling): MiniLM-L6 reads 256 tokens including `[CLS]`/`[SEP]`, silently. P4 adds only 04's proposed check (S7):

| D-004 question vs | cos |
|---|---|
| a 400-token passage whose DAC definition starts at token 300 | 0.019276 |
| the same passage's first 254 tokens (no DAC text) | **0.019276** |
| the tail (tokens 255–400) embedded alone | 0.284787 |

The answer is in the chunk text, but it cannot help the chunk **get retrieved**. Other caps: L3 128 tokens; the cross-encoder 512 (S1); Cohere `embed-v4.0` lists 8192 (O2 report).

> 📖 Now read **book block 2** (Ch13 p.6–7/13 and p.9/13).

### D.7 Bi-encoder vs cross-encoder

| | Bi-encoder (MiniLM-L6) | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
|---|---|---|
| Input | one text at a time | the pair (query, document) together |
| Output | a 384-d vector per text | one relevance score per pair: a raw **logit**, unbounded (−10.97 to 5.17 on a shortlist, S8) |
| Precompute documents? | **Yes**: 91 encodes once at index time | **No**: no stored vector exists |
| Cost per query | 1 model pass (the query) + cheap dot products | 1 pass **per pair**: 10 to rerank a top-10, 91 to score everything (S8) |
| Sees word interactions between query and document? | No: two summaries compared | Yes: attends across both texts (Ch13 p.6/13) |
| Order of inputs | symmetric score | **matters**: CE(q, d) = −4.293 but CE(d, q) = −6.722 (S8) |

**Illustration, not an evaluation (S8).** D-002: the bi-encoder's top-10 had the gold window at rank 2; reranking those 10 with the cross-encoder moved it to **rank 1** (top-3: 26, 64, 63). D-004: gold already at rank 1; unchanged. Two questions prove nothing about quality. **The design:** bi-encoder for recall over the whole collection, cross-encoder for precision on a short list, as in `reranking.ipynb` cells 27–29 (retrieve `k=10`, rerank, keep 5).

> 📖 Now read **book block 3** (Ch6 p.1–2/14).

### D.8 Query/document asymmetry: input types and prefixes

- **The problem** (Ch6 p.1–2/14): a short question and a long declarative chunk embed differently even on the same topic. Illustration (S9): window 26 scores 0.4336 against the D-002 **question** but 0.5135 against a **statement** of the answer. That gap is what HyDE (Ch6) and document augmentation (Ch11 p.1/13) attack.
- **Model-side fix: asymmetric embedding models.** They are trained to embed queries and documents differently, and you must tell them which is which:
  - **Cohere:** `input_type="search_document"` for chunks, `"search_query"` for questions (our decision D-03; [06 §3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#3-v0-baseline-exact-specification)). The O2 smoke test called `embed-v4.0` with `search_document` (dim 1536) ([report](../progress/O2_smoke_test_2026-10-08.json)). **No `search_query` call has been made, so how much the two differ is UNVERIFIED.**
  - **Instruction-prefix models** (e.g. bge's query instruction, [06 §3.2](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#32-embedding-model-facts-and-the-truncation-trap)): a fixed text prepended to queries only. For the repo's `bge-base-en-v1.5`, the recommendation is UNVERIFIED here.
- **A prefix on a model not trained with one just moves the vector** (S9, MiniLM-L6): cos(`"query: "` + q, q) = 0.9626; with `"search_query: "` 0.6965; with bge's instruction 0.6865. Use only the prefix the model card names.
- **Code rule:** keep `embed_query` and `embed_documents` **separate** ([06 §2.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#23-provider-agnostic-interfaces)). `dartboard.ipynb` cell 23 embeds the query with `embed_documents([query])`: harmless for a symmetric model, a silent error for an asymmetric one (J4). The repo never sets an `input_type` anywhere (S-src).

---

## Part E — Connections

**P1** (tokens, `max_seq_length`) and **P2** (query, ranking) → **P4** → **P5** (exact k-NN, FAISS metrics) · **C3** (embed and index; store the model id) · **C4** (score inspection) · reranking (cross-encoders) · HyDE / HyPE / document augmentation (asymmetry).

| Often confused | The difference |
|---|---|
| Similarity vs distance | Cosine/dot: higher = closer. L2: lower = closer. Never feed one where the other is expected (J1). |
| Cosine vs dot | Equal only for unit vectors. Dot rewards long vectors. |
| Normalising **text** vs normalising **vectors** | Ch1 p.5/14 "normalizes" text (cleaning). Vector normalisation divides by the length. |
| Score normalisation (Ch12 p.8/14) vs vector normalisation | Min-max rescales scores **across chunks** for fusion; it does not touch vectors. |
| "Similarity matrix" vs score vector | Retrieval: one query × N chunks → N scores. All-pairs: N × N (dartboard diversity only). |

---

## Part F — Worked example by hand

Use q = [1, 2, 2], d1 = [2, 1, 2], d2 = [0, 3, 4], d3 = [2, 4, 4]. Paper only.

**Step 1.** Compute dot(q, d2) and ‖d2‖.

<details><summary>Answer</summary>

dot = 1·0 + 2·3 + 2·4 = **14**. ‖d2‖ = sqrt(0 + 9 + 16) = **5**. (‖q‖ = sqrt(1 + 4 + 4) = 3.)

</details>

**Step 2.** Compute cos(q, d2) and L2(q, d2).

<details><summary>Answer</summary>

cos = 14 / (3 × 5) = **0.9333**. q − d2 = [1, −1, −2], so L2 = sqrt(1 + 1 + 4) = sqrt(6) = **2.4495** (S2).

</details>

**Step 3.** Do the same for d1 and d3, then rank by cosine and by raw L2.

<details><summary>Answer</summary>

d1: dot 8, cos 8/9 = 0.8889, L2 sqrt(2) = 1.4142. d3: dot 18, cos 18/18 = 1, L2 sqrt(1 + 4 + 4) = 3. Cosine: d3, d2, d1. Raw L2: d1, d2, d3, the reverse (S2).

</details>

**Step 4.** Normalise q and d1. Check that L2² = 2 − 2cos.

<details><summary>Answer</summary>

q̂ = [1/3, 2/3, 2/3]; d̂1 = [2/3, 1/3, 2/3]. Difference [−1/3, 1/3, 0]; L2² = 1/9 + 1/9 = **0.2222**. And 2 − 2 × 8/9 = 2/9 = **0.2222** (S2).

</details>

> 🧭 Coach: CR-08 probe here, one question: "Double the query to [2, 4, 4]. Which ranking changes: dot, cosine or raw L2?" Expected: only raw L2. Dots all double (16, 28, 36), cosines do not change, and raw L2 becomes 3.6056, 2.2361, 0, so it now ranks d3 first (S2). Then ask what that means for a system that uses raw L2 on unnormalised vectors.

---

## Part G — Source connection

### G.1 Book (Source A)

| Cite | Book point (paraphrased) | Our assessment |
|---|---|---|
| Ch1 p.5/14 | An embedding is a list of numbers that captures meaning; similar topics give vectors close together; GPS analogy | Correct intuition; **no metric named** |
| Ch1 p.6/14 | Emissions vs CO₂-in-the-atmosphere chunks land near each other; a "Meaning Space" diagram | Measured: 0.5356 vs −0.0859 for an unrelated phrase (S5) |
| Ch1 p.8/14 | The query is embedded by the same process so that distances mean something | The MC-002 step. Agrees with `json_rag` cell 22 |
| Ch12 p.8/14 | Vector scores are cosine similarities, bounded between −1 and 1; BM25 scores are unbounded | First use of "cosine" in reading order. True range; real values are model-specific (D.5) |
| Ch13 p.6–7/13 | Bi-encoder: separate passes, precomputed documents, compared typically by cosine; cross-encoder: joint input, cannot precompute. Diagram: speed vs accuracy | Matches D.7 and S8. "Accuracy" is a claim to test (CR-07) |
| Ch13 p.9/13 | Cross-encoder rerankers are small trained scorers; rigid, no custom criteria | Fair. Score is a logit, not a probability (S1, S8) |
| Ch6 p.1–2/14; Ch11 p.1/13 | The asymmetry problem: short questions and long answers embed apart; HyDE fixes the query side, document augmentation the document side | Illustrated once (S9). The book never mentions input types or prefixes |
| App p.13–16/23 | Glossary: Asymmetry Problem, Bi-Encoder, Cosine Similarity, Cross-Encoder, Embedding | The cosine entry lists Chapter 1; **Ch1 never says cosine** (DV-B4, confirmed by text search, S-src) |

**Not in the book:** dot product, Euclidean/L2, unit vectors, vector normalisation, `input_type`, prefixes, truncation, `max_seq_length` (S-src).

### G.2 Repo (Source B): cells verified at `009adba`

| Cell (0-based) | What it shows | Lesson |
|---|---|---|
| `json_rag.ipynb` 19, 21, 23 | MiniLM-L6 embeddings into `faiss.IndexFlatL2`; the query encoded by the same model; printed distances, "lower is better" (cell 22) | MiniLM-L6 outputs **unit** vectors (S4), so these L2 distances rank exactly like cosine (D.3, S6). The printed number is a distance, not a similarity |
| `local_rag_huggingface_faiss.ipynb` 10, 13, 14, 16 | `BAAI/bge-base-en-v1.5`; `normalize_embeddings=True` "for cosine"; `FAISS.from_documents` with no metric argument | Normalising makes the default L2 index rank like cosine. No query instruction is used (asymmetry, D.8) |
| `dartboard.ipynb` 23 | Query embedded with `embed_documents([query])`; `1 - np.dot(...)` as "cosine distance" for query–candidates and candidates × candidates | Correct only for unit vectors (toy non-unit: 1 − dot = −17, S2). The K × K matrix is for diversity |
| `graph_rag.ipynb` 12 | `similarity_search_with_score(...)`, then `priority = 1 / similarity_score` in a min-heap | If the score is an L2 distance, the order inverts (S10, J1) |
| `reranking.ipynb` 27, 29 | `CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')` on `[query, doc]` pairs, sorted descending; `k=10`, `rerank_top_k=5` | D.7 |
| `simple_csv_rag.ipynb` 12; `helper_functions.py` L48–L74 | A hand-built `IndexFlatL2`; `encode_pdf` with `OpenAIEmbeddings()` (L73) and `FAISS.from_documents` (L74) | FAISS metric choices: next in P5 |

**FAISS default metric in the repo's usage (S-src):** `IndexFlatL2` in 9 places; **no** `IndexFlatIP` or inner-product metric anywhere; **no** `distance_strategy` override. So every repo FAISS store ranks by L2 distance. That LangChain's `FAISS.from_documents` defaults to L2, and that `IndexFlatL2` returns squared distances, are UNVERIFIED locally (neither library is installed).

**Corrections and additions to the [04 P4 row](../04_BOOK_TO_CODE_MAPPING.md)** (04 is not edited):
1. `json_rag.ipynb` cells 19–23 "raw L2 distances": true, but on unit MiniLM vectors, so the ranking equals cosine. 04 reads as if it were the L2-vs-cosine trap; it is not.
2. `dartboard.ipynb` cell 23: 04 is right that `1 − VVᵀ` assumes unit norm. It misses that the query is embedded with **`embed_documents`** (an asymmetry hazard).
3. `local_rag_huggingface_faiss.ipynb`: the model is set in cell 10 and the store built in cell 16 (no metric); 04 cites only cell 14.
4. Book column: Ch1 p.8/14 (query embedded the same way; in the 02 card), Ch13 p.9/13 and App p.13–14/23 are missing. DV-B4 is confirmed. "Cosine first used Ch12 p.8/14" is right. Both 04 experiment ideas now have numbers (S3, S7).

### G.3 Reading list (in this order)

`json_rag.ipynb` cells 19 → 21 → 23 → `local_rag_huggingface_faiss.ipynb` cells 13–14 → `dartboard.ipynb` cell 23 → `graph_rag.ipynb` cell 12 → `reranking.ipynb` cell 27. For each, write in the margin: model, normalised or not, metric, and whether higher or lower is better.

---

## Part H — Implementation progression

### H.1 The lab: [`labs/P4_embeddings_lab.ipynb`](../labs/P4_embeddings_lab.ipynb) (blank-file first)

The notebook gives the tasks, empty code cells, prediction cells and CHECK cells. It has **no solution code**; the CHECK cells compare fingerprints, so the answers stay hidden until you predict.

| # | Task | The checks test |
|---|---|---|
| 1 | Write `dot`, `norm`, `cosine`, `l2` in plain Python | Unit tests + the toy table of D.2 |
| 2 | Predict, then rank d1–d3 by dot, cosine, raw L2 | The three rankings (S2) |
| 3 | Write `unit`; rank by L2 on unit vectors; write the proof in your words | L2² = 2 − 2cos on your functions; the ranking flips back |
| 4 | CR-08: double the query; predict which ranking changes | Only raw L2 changes |
| 5 | Load MiniLM-L6; find the Normalize module; measure lengths with and without it | 1.0 vs 2.01–3.04 (S4) |
| 6 | Predict, then embed the book's pair and an unrelated pair | The two cosines (S5) |
| 7 | One query vs 91 windows with the same model; then the wrong model | Score shape (91,), top-5, gold rank 2 → 19 (S6) |
| 8 | Bi-encoder top-10, cross-encoder rerank | Reranked top-3; 10 pairs scored (S8) |

API names you may look up: `SentenceTransformer`, `.encode`, `normalize_embeddings`, `SentenceTransformer(modules=[...])`, `CrossEncoder.predict`, `np.linalg.norm`, `np.argsort`. The reference implementation is `sources/verification/P4/p4_measure.py`.

> 🧭 Coach: The reference script is a **solution**. Do not show it before an attempt plus a hint (CR-04). Grade `coding_independence_0_3` on Tasks 1, 3 and 7, and `debugging_0_3` on any failing CHECK the learner fixes.

### H.2 Repo reading guide: the `graph_rag.ipynb` cell 12 inversion (02 evidence)

Trace `_expand_context` for three start nodes with scores A 0.2, B 0.5, C 0.9. Answer each before opening.
1. What does `similarity_search_with_score` return as the score, for a default LangChain FAISS store?
2. What priorities does `1 / similarity_score` give?
3. Which node does the min-heap pop first?
4. Which node is actually closest?
5. What happens if a document matches itself exactly?

<details><summary>Answers</summary>

1. An L2 distance, lower = closer (LangChain default; UNVERIFIED locally, consistent with the repo's L2-only indexes).
2. 5.0, 2.0, 1.11.
3. C (priority 1.11), the **farthest** (S10).
4. A. It is explored **last**, step 3 of 3.
5. Distance 0 → `1 / 0` → `ZeroDivisionError` (S10). Here each retrieved chunk is searched against a store built from the same chunks, so a 0 is plausible; whether it occurs depends on the embedding API returning identical vectors (UNVERIFIED).

**Write-up (02 evidence):** two sentences: what the code assumes, why the assumption fails, and the one-line fix (use `similarity_search_with_relevance_scores`, or `priority = distance`).

</details>

### H.3 Reusable design (future `ragkit/`; nothing is created now)

- `Embedder` with **separate** `embed_query` / `embed_documents`, the `input_type` or prefix inside each ([06 §2.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#23-provider-agnostic-interfaces)).
- Normalise at index time and query time; assert `abs(norm - 1) < 1e-4` on a sample.
- Store `model_id`, revision, `input_type`, `normalized`, `metric` with the index; refuse to query with a different model id (D.5).
- Score functions return a **similarity** (higher = better) everywhere; convert distances once, at the store boundary. Truncation count: [P1 H.3](P1_llm_fundamentals.md#h3-reusable-design-future-ragkit-nothing-is-created-now).

---

## Part I — Controlled experiment

**n/a for P4 (prerequisite concept, toy data only).** P4 changes no pipeline variable on the eval set. Its two-question illustrations (S6, S8) are not results. The reranking and embedding-model comparisons are later experiments.

---

## Part J — Failure and debugging

For each: write your predicted cause and fix, then open. Each diagnosis says whether it is a **retrieval** or a **generation** failure (CR-11).

**J1. The farthest node first.** A graph walk starts from the least relevant chunks (`graph_rag.ipynb` cell 12).

<details><summary>Diagnosis</summary>

- **Cause.** A distance treated as a similarity: `1 / distance` gives far nodes the smallest priority (S10).
- **Kind.** Retrieval (context assembly order).
- **Fix.** Use a similarity score, or use the distance itself as the priority. Assert the score's direction once with a known duplicate.

</details>

**J2. Scores all near zero, no error.** After a model upgrade, every top score is below 0.2.

<details><summary>Diagnosis</summary>

- **Cause.** Query and chunks embedded by different models with the same dimension (S6: 0.46 → 0.19 max; gold rank 2 → 19).
- **Kind.** Retrieval.
- **Fix.** Store the model id with the index; assert it matches at query time; re-embed everything after any model change.

</details>

**J3. Long chunks always win.** Ranking by raw dot product, the longest-vector chunks fill the top-k.

<details><summary>Diagnosis</summary>

- **Cause.** Unnormalised vectors: dot grows with length (toy S3: raw dot top-1 differs from cosine in 68/100 queries).
- **Kind.** Retrieval.
- **Fix.** Normalise both sides; or use cosine. Check the model's modules first (D.4).

</details>

**J4. Cohere retrieval is weaker than expected.** All texts, questions included, were embedded with `input_type="search_document"`.

<details><summary>Diagnosis</summary>

- **Cause.** Asymmetric model used symmetrically (as in `dartboard` cell 23's `embed_documents([query])`). How much it hurts on our corpus is UNVERIFIED.
- **Kind.** Retrieval.
- **Fix.** `search_query` for questions; a separate `embed_query`. Measure both settings on the dev set before claiming a gain.

</details>

> 🧭 Coach: For J1 and J2, ask for the **one-line assert** that would have caught it. It counts as evidence for `debugging_0_3`.

---

## Part K — Engineering decisions

| Question | Decision | Why |
|---|---|---|
| Which similarity? | Cosine, implemented as dot on normalised vectors | Same ranking as L2 on unit vectors (D.3); cheapest |
| Normalise? | Yes, both sides, and assert it | Removes length effects (D.4) |
| FAISS metric (P5) | Inner product on unit vectors, or L2 on unit vectors; never raw L2 on unnormalised vectors | D.3; S3 |
| Query embedding | Same model; `search_query` (Cohere) or the model card's prefix | D.5, D.8 |
| Similarity threshold | None carried across models; set on a labelled dev set | Values are model-specific (D.5) |
| Reranking | Bi-encoder top-k, then cross-encoder on the shortlist | Cost: one pass per pair (D.7) |

**When NOT to rerank with a cross-encoder:** when latency per query is tight and the shortlist is long (one model pass per pair), or when relevance needs custom criteria it was not trained for (Ch13 p.9/13).

---

## Part L — Assessment

One short question per item. Each has a reply template. Score with [05 §4.2](../05_LEARNING_AND_RETENTION_SYSTEM.md#42-graded-rubrics-04).

> 🧭 Coach: Ask one item at a time, with its template. Never put two questions in one turn. Record confidence first.

### L.1 Recall

**P4-R-01** (O1-Q02 check). Write the cosine formula.
*Template:* "cos(a, b) = ____ / ____."

<details><summary>Criteria for 4</summary>

(a · b) / (‖a‖ ‖b‖); range −1..1; measures angle only. Plus: for unit vectors it equals the dot product.

</details>

**P4-R-02** (MC-002 check item). What happens to the user's question at query time?
*Template:* "It is ____ with ____, then ____."

<details><summary>Criteria for 4</summary>

Embedded with the same model (and the query input type if the model has one); one score per chunk; top-k kept. Boundary: a score vector, not an all-pairs matrix.

</details>

**P4-R-03** (O1-Q10 check). Why can a bi-encoder search a whole collection fast but a cross-encoder cannot?
*Template:* "The bi-encoder can ____, but the cross-encoder must ____."

<details><summary>Criteria for 4</summary>

Bi-encoder precomputes document vectors (one query pass per search); cross-encoder needs one pass per (query, document) pair, nothing stored (S8: 10 vs 91 passes). Plus the trade-off: joint reading is more precise (Ch13 p.6/13).

</details>

**P4-R-04.** What does Cohere's `input_type` do?
*Template:* "It tells the model whether the text is ____ or ____, because ____."

<details><summary>Criteria for 4</summary>

Marks a text as a search query or a search document; the model embeds them differently because questions and chunks differ in form (asymmetry, Ch6). Plus: the size of the effect on our corpus is UNVERIFIED.

</details>

### L.2 Application

**P4-A-01** (MC-002 check item). Compute cos(a, b) for a = [3, 0, 4] and b = [0, 0, 5].
*Template:* "dot = ____, lengths ____ and ____, cos = ____."

<details><summary>Criteria for 4</summary>

dot = 20; lengths 5 and 5; cos = 0.8 (derived). Self-check: in −1..1; both vectors have a positive z part, so cos > 0.

</details>

**P4-A-02** (CR-08). You multiply one document vector by 2. What happens to its dot, cosine and L2 with the query?
*Template:* "Dot ____; cosine ____; L2 ____."

<details><summary>Criteria for 4</summary>

Dot doubles (8 → 16); cosine unchanged (0.8889); L2 changes but not by a fixed factor (1.4142 → 3.6056 for d1, S2), so raw-L2 ranks can flip. Self-check: re-compute one number.

</details>

**P4-A-03** (debugging). What is wrong in this code?

```python
q = model_v2.encode([question])[0]       # model_v2 also gives 384 numbers
scores = E_v1 @ q                        # E_v1 built last month with model_v1
```

*Template:* "The bug is ____. The fix is ____."

<details><summary>Criteria for 4</summary>

Query and index from different models; same dimension hides it (S6). Fix: re-embed with one model, or use model_v1 for the query; store and assert the model id.

</details>

### L.3 Transfer

> 🧭 Coach: P4-T-01 is a practice item. For the scored CR-13 item, invent a fresh scenario (another domain, language, modality or constraint) that is not in this file, and grade it with the Transfer rubric.

**P4-T-01.** A help-desk search uses a model that gives vectors of very different lengths. Should it use dot product or cosine?
*Template:* "I would use ____, because ____. I would check it by ____."

<details><summary>Criteria for 4</summary>

- Check first whether length carries meaning for that model (some models are trained for dot product; read the model card). If not, cosine or normalise (D.4; toy S3: 68/100 top-1 changes).
- Trade-off: normalising is cheap; ignoring a meaningful length loses signal.
- Verify by measurement: Recall@k / MRR on labelled help-desk queries, dot vs cosine, retrieval metrics only.
- When not to: if the model card says dot product with unnormalised vectors.

</details>

### L.4 When is P4 mastered?

- **`applied` (L3):** P4-R-01 ≥ 3 on two different days, one ≥ 24 h after teaching; two Application items ≥ 3; `coding_independence_0_3 ≥ 2` on lab Tasks 1, 3, 7.
- **MC-002 closes** when two of its check items (P4-R-02, P4-A-01; later the C4 `top_k` code item) score ≥ 3, unassisted, on different days ([log rule](../progress/misconception_log.md)).
- **`transfer` (L4):** a fresh novel-scenario item ≥ 3; `debugging_0_3 ≥ 2`; a teach-back ≥ 3.

---

## Part M — Retention

### M.1 Flashcards

| # | Front (one question) | Back |
|---|---|---|
| 1 | Cosine formula? | (a · b) / (‖a‖ ‖b‖) |
| 2 | Cosine of a and 2a? | 1 (length ignored) |
| 3 | L2 between unit vectors? | L2² = 2 − 2cos |
| 5 | Is a FAISS `IndexFlatL2` score a similarity? | No: a distance, lower = closer |
| 6 | Does MiniLM-L6 output unit vectors? | Yes: Normalize module; lengths 1.0 (S4) |
| 7 | What is embedded at query time? | The question, with the same model |
| 9 | Wrong model, same dim? | No error; gold rank 2 → 19 (S6) |
| 10 | Bi-encoder precomputes…? | Document vectors |
| 11 | Cross-encoder cost? | One model pass per (query, doc) pair |
| 12 | Cohere input types? | `search_document` chunks, `search_query` questions |

### M.2 Retrieval practice (closed book; log per [05 §5.1](../05_LEARNING_AND_RETENTION_SYSTEM.md#51-active-recall-what-a-review-item-looks-like))

| When | One question | Template |
|---|---|---|
| Day 1 | Write the cosine formula. | "cos = ____ / ____" |
| Day 3 | Why do L2 and cosine rank unit vectors the same? | "Because L2² = ____." |
| Day 7 | Compute cos([1, 0, 1], [1, 1, 0]). (Answer: dot 1, lengths √2 and √2, cos 0.5; derived.) | "dot ____, lengths ____, cos ____" |
| Day 14 | When would you use a cross-encoder, and when not? | "Use it to ____; not when ____." |

### M.3 Teach-back prompt ([05 §5.4](../05_LEARNING_AND_RETENTION_SYSTEM.md#54-teach-back-protocol))

"In 3 minutes, explain to a teammate how one question is scored against our chunks, and why we normalise." A 4 needs: same model for the query; one score per chunk; cosine formula; L2² = 2 − 2cos; one measured number; one failure mode (wrong model or distance-as-similarity).

### M.4 Interleaving links

- **P1:** count the D-004 passage's tokens; where does the cap fall? (S7)
- **P5:** rank with `np.argpartition` on `E @ q`; compare with the full sort.
- **P3 / fusion:** cosine is bounded, BM25 is not (Ch12 p.8/14), so scores need rescaling before fusing.

### M.5 Misconception-log entries to add when observed

| Label | Correct model (short) | Root cause | Severity | Check items |
|---|---|---|---|---|
| "Lower score = worse, always" | Depends on similarity vs distance | terminology | medium | P4-A4, J1 |
| "Same dimension = compatible" | Same model required | over-generalisation | high | P4-A-03, J2 |
| "Cosine and dot are the same" | Only for unit vectors | over-generalisation | medium | P4-A-02 |

### M.6 Progress-tracker entry (format only; fictional values, per [05 §6.1](../05_LEARNING_AND_RETENTION_SYSTEM.md#61-progressconcept_trackercsv))

```csv
P4,Embeddings & similarity,1,E,exposed,<YYYY-MM-DD>,,,<YYYY-MM-DD +1>,1,,,,,,,na,MC-002,1,log:<YYYY-MM-DD>#P4-R-01
```

---

## Source references

**Book (Source A).** Ch1 p.5/14, p.6/14, p.8/14; Ch6 p.1/14, p.2/14; Ch11 p.1/13; Ch12 p.8/14; Ch13 p.6/13, p.7/13, p.9/13; App p.13/23, p.14/23, p.15/23, p.16/23. Checked against the PyMuPDF page text by `p4_sources.py` on 2026-10-08. Paraphrased; no quotation reaches 15 words.

**Repo (Source B)**, `NirDiamant/RAG_Techniques` @ `009adba2be1bef49780ef73b6dd3c18fd24b035b`, cells 0-based, all in `all_rag_techniques/`: `dartboard.ipynb` 23; `json_rag.ipynb` 19, 21, 22, 23; `local_rag_huggingface_faiss.ipynb` 10, 13, 14, 16; `graph_rag.ipynb` 12; `reranking.ipynb` 27, 29; `simple_csv_rag.ipynb` 12; plus `helper_functions.py` L48, L73, L74; `data/Understanding_Climate_Change.pdf` (sha256 `1d58a0fa…92669`).

**Our records.** [P1 D.4](P1_llm_fundamentals.md#d4-embedding-truncation-what-minilm-actually-reads); [07 D.6](../07_SAMPLE_LESSON.md#d6-embedding-truncation-the-hard-ceiling); [`progress/O2_smoke_test_2026-10-08.json`](../progress/O2_smoke_test_2026-10-08.json); [06 §3.2](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#32-embedding-model-facts-and-the-truncation-trap); 08 D-03; [session log, O1](../progress/session_log.md). **Supplementary (Source C, external; not needed for any claim):** C#16–#21 (SBERT, DPR, MTEB), C#52 (Cohere input types) ([01 §6](../01_SOURCE_INVENTORY.md#6-source-c--supplementary-references-external)).

---

## Verification log

**Environment.** Run on 2026-10-08 with `uv run` from `rag_learning/`: CPython 3.12.8, pymupdf 1.26.7, transformers 5.19.0, sentence-transformers 6.1.0, torch 2.14.1 (CPU), numpy 2.5.3. Models offline from the HF cache: all-MiniLM-L6-v2 `1110a243…` (as in P1/07), paraphrase-MiniLM-L3-v2 `4ca70771…`, ms-marco-MiniLM-L-6-v2 `233902d2…`. No Groq or Cohere call; `.env` not read. FAISS and LangChain are not installed and were not run.

| Claim | How verified |
|---|---|
| All S1–S10 numbers | **Ran** `p4_measure.py`; output `out_p4_measure.txt`; a second run was **byte-identical** |
| L2² = 2 − 2cos; unit-vector outputs of MiniLM-L6 (not L3) | **Derived** (D.3) and **ran** (S2, S3 100/100, S6 4.77e-07; S1 modules, S4 lengths) |
| Every repo cell, book page, repo-wide metric count and book absence | **Ran** `p4_sources.py`: ALL PASS (`out_p4_sources.txt`) |
| DV-B4 (glossary says Ch1 explains cosine) | **Confirmed**: no Ch1 page contains "cosine" |
| Lab CHECK cells | **Ran** with a throwaway solution outside the workspace: 9/9 pass; 5 broken variants fail at the intended CHECK |
| 04 P4 row | Cells match; five additions/corrections (G.2) |
| Cohere `input_type="search_document"`, dim 1536; worked-example and L/M arithmetic | **Cited** from the O2 report; **derived** in the text |

**Still UNVERIFIED:**
- how much Cohere `search_query` and `search_document` vectors differ, and the effect on our retrieval;
- LangChain `FAISS.from_documents` defaulting to L2, and `similarity_search_with_score` returning that distance (the basis of the `graph_rag` inversion);
- FAISS `IndexFlatL2` returning squared distances (ranking is unaffected);
- OpenAI embeddings being unit length (what `dartboard` cell 23 assumes);
- the query-instruction recommendation for `bge-base-en-v1.5`;
- whether `graph_rag` cell 12 actually hits a zero distance in practice.
