# Embedding fit check

**What this is:** an automatic check of whether an embedding setup suits these documents and questions, measured on your own chunks.
**What this is not:** an evaluation. A few labelled questions show the mechanism; decide with many questions per type.

**Recommendation:** Mechanism only, not enough data: label at least 10 questions with an expect text before deciding anything. (section 7). Checklist: C1 ✓ C2 ✓ C3 ? C4 ? C5 ✓ C6 ✗ C7 ✓ C8 ? C9 ✓ C10 ✗ C11 ? C12 ?.

Settings: model `sentence-transformers/all-MiniLM-L6-v2` · chunker `v0` (1000 characters, overlap 200) · k 4 · rerank `cross-encoder/ms-marco-MiniLM-L-6-v2` · dims [256, 128] · int8 · threshold 0.5 · sentence-transformers 6.1.0, numpy 2.5.3, pymupdf 1.26.7. No API call.
Documents: `Understanding_Climate_Change.pdf` (33 page(s), 72,561 characters).

## 1 Setup

| Field | Value | Why it matters (lesson step) |
|---|---|---|
| Model | `sentence-transformers/all-MiniLM-L6-v2` (snapshot 1110a243) | store it with the index (4) |
| Numbers per vector | 384 | memory: 1,536 bytes per float32 vector (10) |
| Length limit | 256 tokens | text past it is ignored (6) |
| Modules | Transformer, Pooling, Normalize | |
| Pooling | mean | how token vectors become one vector (2) |
| Normalize module | yes | without it, normalise yourself (3) |
| Prompts | {"query": "", "document": ""} | the question side's label (7) |
| Similarity it declares | cosine | use the one it was trained with (5) |

## 2 Chunks vs the limit

97 chunks; tokens per chunk (the model's tokenizer, special tokens included): min 59, median 149, max 182. Over the 256-token limit: **0**. Longer than 128 tokens: 70 (some models were trained on 128; fits is not the same as well represented).

## 3 Vectors

- Lengths as returned: 1.000000 to 1.000000 (max |‖v‖ − 1| = 1.19e-07). Scores below use normalised vectors (cosine).
- Self-retrieval test: 5 of 5 sampled chunks (#0, #24, #48, #72, #96) rank themselves first.
- Near-duplicates (cosine > 0.98): 0.
- Chunk-against-chunk median cosine (analysis, not search): 0.3906.

## 4 Per question

| Question | Type | Best score | Median score | Top 4 (score) | Right chunk | Rank |
|---|---|---|---|---|---|---|
| D-001: According to the document, by how much have global temperatures risen  | draft-seed | 0.4929 | 0.1751 | #1 0.493 · #0 0.471 · #7 0.469 · #8 0.461 | #7 | 3 |
| D-002: In what year was the Paris Agreement adopted? | draft-seed | 0.4606 | 0.0289 | #69 0.461 · #68 0.451 · #27 0.439 · #17 0.439 | #27 | 3 |
| D-003: According to the document, what is essential regarding countries' nati | draft-seed | 0.6497 | 0.1835 | #68 0.650 · #27 0.632 · #17 0.535 · #69 0.479 | #68 | 1 |
| D-004: What does DAC stand for, and what does it do? | draft-seed | 0.4210 | 0.0492 | #67 0.421 · #23 0.404 · #68 0.360 · #27 0.214 | #23, #67 | 1 |
| D-005: How does the document contrast coal and natural gas in terms of carbon | draft-seed | 0.4272 | 0.1332 | #3 0.427 · #4 0.358 · #2 0.352 · #5 0.319 | #3, #4 | 1 |
| D-006: What are the advantages of putting solar panels on lakes or reservoirs | draft-seed | 0.5331 | 0.2216 | #21 0.533 · #64 0.500 · #14 0.477 · #13 0.470 | #21 | 1 |
| D-007: What is the supreme decision-making body of the convention that provid | draft-seed | 0.7094 | 0.2202 | #69 0.709 · #27 0.611 · #85 0.595 · #84 0.590 | #27, #85 | 2 |
| D-008: What does the Kigali Amendment target? | draft-seed | 0.2598 | 0.0963 | #28 0.260 · #69 0.254 · #58 0.248 · #12 0.204 | #69 | 2 |
| D-009: In what year was the IPCC established? | no-answer | 0.3099 | 0.0662 | #85 0.310 · #27 0.280 · #69 0.274 · #84 0.257 | - | - |
| D-010: What share of global greenhouse gas emissions comes from aviation? | no-answer | 0.5196 | 0.2500 | #2 0.520 · #1 0.434 · #5 0.406 · #85 0.404 | - | - |

## 5 Measuring

8 labelled question(s). MRR@10 counts a rank above 10 as 0.

| Arm | Group | n | Hit@1 | Hit@4 | MRR@10 | Top-4 overlap with base |
|---|---|---|---|---|---|---|
| base | all | 8 | 4 | 8 | 0.708 | - |
| base | draft-seed | 8 | 4 | 8 | 0.708 | - |
| rerank | all | 8 | 8 | 8 | 1.000 | - |
| rerank | draft-seed | 8 | 8 | 8 | 1.000 | - |
| dims 256 | all | 8 | 4 | 8 | 0.750 | 0.90 |
| dims 256 | draft-seed | 8 | 4 | 8 | 0.750 | - |
| dims 128 | all | 8 | 2 | 7 | 0.583 | 0.82 |
| dims 128 | draft-seed | 8 | 2 | 7 | 0.583 | - |
| int8 | all | 8 | 5 | 8 | 0.760 | 0.82 |
| int8 | draft-seed | 8 | 5 | 8 | 0.760 | - |

## 6 Checklist

| Check | Verdict | Evidence | How to check |
|---|---|---|---|
| C1 No chunk is longer than the model's limit | ✓ | 0 of 97 chunks exceed 256 tokens; token counts 59–182, median 149 | count tokens with the model's own tokenizer; shorten chunks or pick a longer-context model |
| C2 Vectors are length 1, or normalised by us | ✓ | lengths as returned 1.000000–1.000000 | max |‖v‖ − 1| over the chunk vectors |
| C3 Questions and chunks use the same model id | ? | this tool embeds both sides with one model; pass --manifest with your index's model_id to check your own pipeline | store the model id with the index and compare it at query time |
| C4 The question side has its label | ? | the model config has no query prompt; read the model card for a query instruction or input type | Cohere: input_type; sentence-transformers: encode_query / encode_document |
| C5 The score direction is understood | ✓ | self-retrieval: 5 of 5 sampled chunks rank themselves first (cosine 1) | search a chunk's own text: it must come back first |
| C6 No threshold copied from elsewhere | ✗ | threshold 0.5 lies inside the best-score range 0.2598–0.7094 | a cut inside the spread keeps some non-answers and drops some answers: set it on labelled data, if at all |
| C7 Near-duplicate chunks are known | ✓ | 0 chunk pairs above cosine 0.98 | remove or merge duplicates; they waste top-k places |
| C8 The right chunk is found (labelled questions) | ? | 8 labelled question(s): Hit@4 8/8, MRR@10 0.708; fewer than 10 shows a mechanism, not a result | label at least 10 questions with an expect text |
| C9 A reranker was tried | ✓ | top-10 rerank: Hit@1 4 → 8 of 8 (4 questions gained rank 1, 0 lost it); MRR@10 0.708 → 1.000 | rerank the bi-encoder's top 10 with a cross-encoder; compare Hit@1 and MRR |
| C10 Smaller vectors were measured before use | ✗ | dims 256: top-4 overlap 0.90, Hit@4 8/8; dims 128: top-4 overlap 0.82, Hit@4 7/8; int8: top-4 overlap 0.82, Hit@4 8/8 (base Hit@4 8/8) | keep a smaller setting only if top-k overlap ≥ 0.9 and Hit@k does not drop |
| C11 Negations and exact codes were tested | ? | no question typed exact-term, negation or code; embeddings blur negation and rare exact strings | write 2 negated and 2 code/number questions; compare with keyword search (bm25_fit_check.py) |
| C12 Licence, privacy and cost are clear | ? | model licence (model card): apache-2.0; local model, no API cost; no text left this computer | read the licence; never send private or book text to an API; count calls and tokens before an API run |

✓ fine · ✗ problem found · ? check by hand.

## 7 Recommendation

Mechanism only, not enough data: label at least 10 questions with an expect text before deciding anything.

Lesson: `study/lessons/P4_embeddings.html`. This report is a mechanism check on your data, not an evaluation result.
