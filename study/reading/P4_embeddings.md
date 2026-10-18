<!-- kit:reading concept=P4 depth=short version=1 -->
# P4: Embeddings and similarity

**What this is:** the short reading for P4, the text version of the HTML lesson's Short depth (`study/lessons/P4_embeddings.html`). It is enough to answer every question in `study/questions/P4_questions.md`.
**What this is not:** the full lesson with the lab (`concepts/P4_embeddings_similarity.md`), or the training maths, compression details and repo walk-through that the HTML lesson keeps in Full.

> **Read in the book:** Ch1 p.5–6/14 and p.8/14 before §2; Ch6 p.1–2/14 before §7; Ch13 p.6–7/13 and p.9/13 before §8; the glossary App p.13–16/23 at the end.

Every measured number here comes from local runs with MiniLM (`all-MiniLM-L6-v2`) on the climate PDF: `sources/verification/P4/P4_FACTS.md`, sections S1–S10 and K1–K13. The running example is draft question **D-002**, "In what year was the Paris Agreement adopted?", against v0's **97 chunks**. The draft questions were written by an LLM and are not yet checked by you, so every rank below is an observation, not an evaluation result. No API was called to write this file.

## 1. Three bugs that raise no error

**The answer first:** embedding code almost never crashes. It returns numbers, they get sorted, and a list of chunks comes back, so its mistakes survive unnoticed.

Three of them, measured or reproduced on the course's own material:

1. **The wrong model for the question.** The 8 answerable draft questions were embedded with a different 384-number model (`paraphrase-MiniLM-L3-v2`, "L3") and compared with chunk vectors made by MiniLM. Python raised nothing, because both give 384 numbers. The right chunk was in the top 4 for 8 of 8 questions before and 3 of 8 after; D-002's right chunk fell from rank 3 to rank 16 of 97 (K3, K4). L3 used with its *own* chunk vectors still found 8 of 8: the model is not bad, the mix is.
2. **A distance read as a similarity.** The repo's `graph_rag.ipynb` (cell 12) takes the score of a LangChain FAISS search and explores the chunk with the smallest `1 / score` first. That score is a distance, where smaller means closer, so the closest chunk is explored last (toy scores 0.2, 0.5, 0.9, S10).
3. **Text past the limit.** MiniLM reads only the first 256 tokens. A 400-token passage whose definition of direct air capture starts at token 300 scores 0.019276 against "What does DAC stand for, and what does it do?", and so do its first 254 tokens on their own (S7). The answer was in the text and changed nothing.

**For your project:** each bug has a one-line check (§12). v0 stores the model id next to the index and refuses to query it with another model (C3).

## 2. An embedding is an arrow

**The answer first:** an embedding model turns a text into a fixed-length list of numbers, a vector. Think of it as an arrow from the origin; texts about the same thing point the same way.

MiniLM returns 384 numbers for any text; Cohere's `embed-v4.0`, the course default, returns 1,536. MiniLM gets there in two moves: its transformer makes one vector per token, then it averages them (**mean pooling**) into one vector for the whole text (K1). The book calls this coordinates in a space of meaning (Ch1 p.5–6/14).

Three ways to compare two arrows a and b:

| Measure | Looks at | Formula | Closer means |
|---|---|---|---|
| Cosine | the angle only | `a·b / (‖a‖ ‖b‖)` | higher (1 same direction, 0 right angle, −1 opposite) |
| Dot product | the angle and both lengths | `Σ aᵢbᵢ` = cos × ‖a‖ × ‖b‖ | higher; longer arrows score more |
| L2 distance | the gap between the tips | `√Σ (aᵢ − bᵢ)²` | lower (0 = the same point) |

By hand, with q = [1, 2, 2] (toy, S2):

```
doc  vector        length  dot   cos      L2
d1   [2, 1, 2]     3       8     0.8889   1.4142
d2   [0, 3, 4]     5       14    0.9333   2.4495      14 / (3 × 5) = 0.9333 ; q − d2 = [1, −1, −2] → √6
d3   [2, 4, 4]=2q  6       18    1.0000   3.0000
```

Cosine ranks d3, d2, d1. Raw L2 ranks d1, d2, d3, the exact reverse: d3 points exactly along q but is twice as long, so its tip is far away. Double d1 and its dot doubles (8 → 16), its cosine stays 0.8889, and its L2 changes by no fixed rule (1.4142 → 3.6056).

**The tempting wrong idea:** "cosine and dot product are the same." They are equal only when both arrows have length 1.

## 3. Normalise, and read the direction

**The answer first:** divide every vector by its length (normalise) and the three measures give the same ranking. Then check which way your library's score runs.

For two unit vectors (length 1):

```
‖â − b̂‖² = 1 + 1 − 2·â·b̂ = 2 − 2·cos        and        â·b̂ = cos
```

So as cosine rises, L2 falls, always: the smallest distance and the largest cosine belong to the same chunk. Toy check: unit-vector L2 to d1, d2, d3 is 0.4714, 0.3651, 0, and 0.4714² = 0.2222 = 2 − 2 × 0.8889. On 100 random questions × 1,000 random documents, cosine and unit-vector L2 gave the identical full ranking 100 times out of 100 (S3).

**Check, do not assume, that vectors have length 1** (97 chunks, K2): MiniLM as shipped ends with a Normalize module and gives 1.000000 every time; the same model with that step removed gives 2.05 to 3.27; L3 has no Normalize module and gives 2.36 to 3.47. On raw vectors the measures disagree: D-002's right chunk went to rank 1 under raw dot and rank 4 under raw L2 (K3). Over the 8 questions the changes went both ways, which is noise. The reason to normalise is that the score then means one thing, not that it scores better. When lengths vary 0.5–2×, raw L2's top result changed for 94 of 100 toy questions and raw dot's for 68 of 100 (S3).

**Every library has a convention** (library source and docs; values with MiniLM, K5). For "greenhouse gas emissions" vs "a recipe for chocolate cake":

| Library call | Returns | Closer means | Value |
|---|---|---|---|
| cosine (sentence-transformers' default) | cosine | higher | −0.0859 |
| FAISS `IndexFlatL2`, and LangChain's FAISS by default | **squared** L2 | **lower** | 2.1719 |
| sentence-transformers `"euclidean"` | −L2 | higher | −1.4737 |
| LangChain relevance score on FAISS | 1 − d/√2 with d = squared L2 | higher, can be **below 0** | −0.5357 |
| LangChain `InMemoryVectorStore` | cosine | higher | −0.0859 |

LangChain's 1 − d/√2 assumes d is the true L2 of unit vectors (0 to 2). FAISS gives it the squared distance (0 to 4), so the "relevance" turns negative whenever the cosine is below 1 − 1/√2 ≈ 0.293, and can reach −1.83. For D-002, 91 of the 97 chunks are under 0.293. Worked example: two unit vectors with cosine 0.6 have squared L2 = 2 − 1.2 = 0.8 (FAISS reports 0.8), and LangChain's relevance on it is 1 − 0.8/1.4142 = 0.434.

**A one-line test of direction:** search for a chunk's own text. It must come back first, with cosine 1 or distance 0 (all 97 chunks pass with MiniLM).

**For your project:** v0 normalises, asserts the lengths, and scores by dot product (= cosine). Inside the pipeline every score is a similarity; distances are converted once, at the store boundary.

## 4. One score per chunk

**The answer first:** at query time the question goes through the same model as the chunks, and one multiplication gives one score per chunk: a list of N numbers, not a matrix.

At **index time**, once, every chunk is embedded into a matrix E with one row per chunk (97 × 384). At **query time** the question is embedded by the same model (Ch1 p.8/14) into q (384 numbers), and `s = E · q` has shape (97,). Sorting gives D-002's top 5 (K3):

```
rank  chunk  cosine   what it is about
1     69     0.4606   the Kyoto Protocol and the year IT was adopted
2     68     0.4513   the Paris Agreement's goals, no year
3     27     0.4386   the Paris Agreement, adopted in 2015  ← the answer (page 10)
4     17     0.4385   climate policy naming the Paris Agreement, no year
5     84     0.3387   policy instruments
```

Chunk 69 has the shape of an answer ("a treaty, adopted in a year") about the wrong treaty: close in meaning is not the same as answering.

Three measures say how well a search went (P6 owns them): the **rank** of the first right chunk (3 here); **Hit@k** = 1 if that rank is k or better (Hit@4 = 1); **MRR**, the mean of 1/rank over many questions (one question: 1/3 = 0.333). Over the 8 answerable draft questions MiniLM gets Hit@4 for 8 of 8 and MRR@10 = 0.708 (K4).

**Where a real N × N matrix appears:** in training (B × B for a batch of B pairs, §5), in the repo's `dartboard.ipynb` (cell 23, K × K among candidates, for diversity), and in analysis (97 × 97 = 9,409 scores to find near-duplicates; the closest pair here scores 0.8590, K6). Never in the search itself.

**The tempting wrong idea (MC-002):** "retrieval builds a similarity matrix." One question, one score per chunk.

## 5. Where the closeness comes from

**The answer first:** an embedder learned closeness from pairs of texts that belong together; "close" means "the kind of pair its training data paired".

MiniLM's model card says it started from a general language model and was trained on over a billion sentence pairs. In each step it saw a batch of 1,024 pairs, computed the cosine of every question against every partner in the batch, and was penalised unless the true partner scored highest. This is **contrastive** training: pull true pairs together, push the rest of the batch apart. Training texts were cut at 128 tokens.

Two consequences. **Use the similarity the model was trained with:** MiniLM was trained with cosine, which is why it ships with a Normalize step; DPR, a well-known retriever, was trained with the dot product. And training builds exactly the matrix that search never does. A toy batch of 4 draft questions with their right chunks, scored by MiniLM (K10):

```
           chunk 27  chunk 23  chunk 21  chunk 69
D-002      0.4386   -0.0065   -0.0837    0.4606   ← the true pair (27) is not the row's maximum
D-004      0.2136    0.4035   -0.0315    0.0964
D-006      0.1202    0.3313    0.5331    0.1391
D-008      0.1716   -0.0716   -0.0409    0.2535
```

Training wants each row's largest number on the diagonal: true for 3 of the 4 rows. The D-002 row has a high loss, so training on it would push chunk 69 away and pull 27 closer.

**An embedder is not a chatbot.** MiniLM is an **encoder**: it reads the whole text at once and outputs vectors. The course's LLM, `gpt-oss-20b`, is a **decoder**: it predicts the next token and writes text. (Some newer embedders are built from decoders; what makes a model an embedder is that it outputs vectors trained for comparison.)

## 6. Text past the limit

**The answer first:** a model reads at most a fixed number of tokens; anything after that is dropped without an error, so it cannot help the chunk get found.

MiniLM's limit is 256 tokens, counting [CLS] and [SEP], so 254 tokens of text. The DAC test above (§1) shows the effect: 0.019276 with and without the answer; the dropped tail alone scores 0.284787 (S7). The generator would still read the whole chunk if it were retrieved; the limit hurts retrieval, not reading.

v0 with MiniLM is safe: the 97 chunks have 59 to 182 tokens, none over 256 (K7). Two cautions:
- **Fits is not well represented:** 70 of the 97 chunks are longer than the 128 tokens MiniLM was trained on. Whether that costs quality here is not measured.
- **The limit belongs to the model:** L3 stops at 128 and would cut 70 of 97. Cohere's `truncate` setting defaults to `END`, which silently drops the end of a long text; `NONE` makes it an error.

**For your project:** count every chunk's tokens with the embedder's own tokenizer before indexing, and use `truncate="NONE"` for Cohere in experiments.

## 7. Questions may need their own label

**The answer first:** a short question and a long passage look different even on one topic, so some models must be told which side a text is on.

The book calls this the asymmetry problem (Ch6 p.1–2/14). On D-002 (K8): chunk 27 scores 0.4386 against the question and ranks 3; against the statement "The Paris Agreement was adopted in 2015." it scores 0.4775 and ranks 1.

| Model | How you mark the side | If you forget |
|---|---|---|
| Cohere embed-v4.0 | `input_type="search_document"` for chunks, `"search_query"` for questions (required for v3 and newer) | allowed and silent; the cost on our corpus is UNVERIFIED until the recorded run |
| models with an instruction prefix (e.g. bge) | a fixed text before questions, named in the model card | a weaker match, no error |
| MiniLM (symmetric) | nothing | nothing happens |

sentence-transformers 6.1 has `encode_query()` and `encode_document()`, which add a model's prompts if it has any; MiniLM has none, so they equal `encode()` exactly (K8). A prefix on a model not trained with one just moves the vector: "query: " + D-002 has cosine 0.9626 with the plain question; bge's instruction gives 0.6865 (S9).

**The tempting wrong idea:** "same model means the same call for both sides." The repo's `dartboard.ipynb` (cell 23) embeds the question with `embed_documents([query])`: harmless for MiniLM, a silent error for an asymmetric model.

**For your project:** the course's embedder has separate `embed_query` and `embed_documents`, each setting its own input type (06 §2.3).

## 8. Bi-encoder vs cross-encoder

**The answer first:** a bi-encoder embeds each text alone, so chunk vectors are stored once and search costs one model pass; a cross-encoder reads question and chunk together, which is more precise but costs one pass per pair, so it only reranks a shortlist.

The book describes both (Ch13 p.6–7/13). The repo's reranker is `cross-encoder/ms-marco-MiniLM-L-6-v2` (K9):

| | Bi-encoder (MiniLM) | Cross-encoder |
|---|---|---|
| Input | one text | the pair (question, chunk) |
| Output | 384 numbers per text | one raw **logit** per pair, unbounded (−11.06 to 3.27 on D-002's top 10) |
| Stored in advance? | yes: 97 vectors | no: nothing exists before the question |
| Passes per question | 1, then cheap multiplications | 10 to rerank a top 10; 97 for every chunk; 1,000,000 for a million |
| Input order | does not matter | matters: −4.361 vs −3.321 for (question, chunk 69) vs (chunk 69, question) |

Used together (the repo's `reranking.ipynb`, cells 27 and 29: fetch 10, keep 5): on D-002 the reranker moved chunk 27 from rank 3 to rank 1; over the 8 draft questions the right chunk was first for 4 before and 8 after. An illustration only: the draft questions are easy. The Sentence-BERT paper (external) puts the gap at about 65 hours of cross-encoder passes vs about 5 seconds with sentence embeddings, to find the most similar pair among 10,000 sentences. A cross-encoder also needs fine-tuning for any new definition of relevance (Ch13 p.9/13).

## 9. A score is not a probability

**The answer first:** a cosine orders the chunks for one question under one model; it does not say how relevant a chunk is, and a threshold does not carry across models or questions.

MiniLM's scores, measured (S5, K4, K6):
- sentence pairs: unrelated −0.0859 and −0.0478; the book's emissions vs CO₂ pair 0.5356 (Ch1 p.6/14); a paraphrase 0.6918; **"temperatures have risen" vs "… have not risen" 0.8436**, the highest of all;
- best chunk per draft question: 0.2598 to 0.7094 for the answerable ones; **D-010** (aviation's share of emissions, not in the PDF) gets **0.5196**, above the best score of 5 of the 8 answerable questions;
- the median score of a question over all 97 chunks runs from 0.03 (D-002) to 0.25 (D-010).

So no threshold separates "found" from "not found" here: a cut at 0.5 keeps a non-answer and drops real answers. Compare scores within one question and one model. Embeddings also blur negation and rare exact strings (codes, version numbers), which keyword search handles (P3).

**For your project:** v0 uses no similarity threshold. Deciding "no answer in the documents" is a generation-side job (P7, C5).

## 10. Smaller vectors

**The answer first:** you can keep fewer numbers or store each in fewer bits; both save memory, a cut vector must be rescaled to length 1, and both must be re-measured.

A 1,536-number float32 vector takes 6,144 bytes; 2 million of them take 12.3 GB (K13).

**Keep fewer numbers.** Models trained so that the first numbers still work alone are called **Matryoshka** embeddings; Cohere says embed-v4.0 is one, with 256, 512, 1,024 or 1,536 through `output_dimension` (external). MiniLM was not trained that way (K11):

```
numbers kept   length after the cut   top 5 same, dot vs cosine   MRR@10 (rescaled)   D-002 rank
384            1.000                  8 of 8                      0.708               3
256            0.771–0.869            4 of 8                      0.750               2
128            0.511–0.642            2 of 8                      0.583               2
32             0.207–0.404            0 of 8                      0.358               23
```

A cut vector is shorter than 1, so dot and L2 stop ranking like cosine: **rescale every cut vector** (questions and chunks). And a model not trained for cutting falls apart when cut hard. (The rise at 256 is noise on 8 draft questions.)

**Fewer bits.** int8 keeps 1 byte per number (4× smaller), binary 1 bit (32×): 1,536 → 384 → 48 bytes for MiniLM. On the 8 questions int8 kept on average 4.4 of float's top 5 and binary 4.1, every right chunk still in the top 4 (K12).

**For your project:** v0 uses the full 1,536 floats; a smaller setting is a later experiment (D2), kept only if top-k overlap and Hit@k stay level.

## 11. Choosing a model and its cost

**The answer first:** the public leaderboard (MTEB) helps you shortlist; your own labelled questions decide.

MTEB's first version covered 8 task types, 58 datasets and 112 languages, and found that no method won everywhere (external). In the larger MMTEB (over 500 tasks), the best public model had 560 million parameters, smaller than several embedders built from LLMs: bigger is not automatically better. The repo picks bge-base because it ranked high on MTEB (`local_rag_huggingface_faiss.ipynb` cell 10). An average over many datasets hides your domain, so shortlist from the retrieval tasks and compare two models on your own questions with the same chunks.

The course uses Cohere embed-v4.0 by default and MiniLM as the local fallback (D-03), and keeps v4.0 although newer models are listed, because switching means re-embedding everything. To call it (Cohere docs, read 2026-10-17): `input_type` (required), `output_dimension` (default 1,536), `embedding_types` (default float), `truncate` (default END), at most **96 texts per call**. Cohere's docs do not say whether its vectors have length 1, so normalise and assert anyway. The price is not on Cohere's pricing page; third-party lists say $0.12 per million tokens (UNVERIFIED).

```
calls  = ⌈n / 96⌉            10,000 chunks → 105 calls
tokens = n × tokens per chunk   10,000 × 250 = 2,500,000 → about $0.30 at the unverified price
```

**For your project:** never switch embedders in the middle of an experiment. The Cohere comparison with MiniLM is left empty until the LLMOps notebook records it; the book's text is never sent.

## 12. Defaults and one-line checks

| Decision | Default |
|---|---|
| similarity | dot product on unit vectors (= cosine) |
| normalise | both sides, then assert |
| score direction | similarity inside the pipeline; distances converted once |
| question model | the index's model id, with its query label |
| length | count tokens with the model's tokenizer; Cohere `truncate="NONE"` |
| threshold | none carried across models or questions |
| dimensions | full floats until measured |
| reranking | a cross-encoder on the bi-encoder's shortlist (R3) |

```python
assert np.allclose(np.linalg.norm(E, axis=1), 1, atol=1e-3)    # unit length
assert index_meta["model_id"] == query_model_id                # same model
assert scores.shape == (len(chunks),)                          # one score per chunk
assert np.argmax(E @ E[i]) == i                                # a chunk finds itself first
assert max(n_tokens(c) for c in chunks) <= max_seq_length      # nothing cut
assert E.shape[1] == cfg["output_dimension"]                   # the dimension you asked for
```

## 13. When not to rely on embeddings alone

- Questions with exact codes, version numbers or rare names: keyword search (P3), or both together (R1).
- Questions that hinge on negation or numbers: the vectors see the topic, not the claim (§9).
- Deciding that no answer exists: not a cosine threshold (§9).
- A small final shortlist where precision matters most: add a cross-encoder (R3).

## Check yourself

→ `study/questions/P4_questions.md` (the HTML lesson's three quick checks come first). Verify every number yourself: `study/notebooks/P4_embeddings_verify.ipynb`. Use the checks on your own documents: `study/tools/embed_fit_check.py`.
