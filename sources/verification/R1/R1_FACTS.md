# R1_FACTS — what the R1 lessons can rely on (run-verified)

Run date: **2026-10-17**. Every number in [`concepts/R1_hybrid_fusion.md`](../../../concepts/R1_hybrid_fusion.md), [`study/reading/R1_hybrid_fusion.md`](../../../study/reading/R1_hybrid_fusion.md) and [`study/questions/R1_questions.md`](../../../study/questions/R1_questions.md) is listed here with the script and output section that produced it. Numbers not produced by these runs are marked DERIVED (arithmetic in the lesson), TOY, or UNVERIFIED.

**Labels.** *Draft-seed observation*: measured on the 10 `llm-draft` seed items of 06 §6.7; for learning, never an evaluation result. *Demonstration*: a hand-picked query; its target is any chunk containing a string. *TOY*: made-up numbers.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment. Nothing was installed.
- **Versions** (printed in S1): pymupdf 1.26.7 · numpy 2.5.3 · rank-bm25 0.2.2 · sentence-transformers 6.1.0 · torch 2.14.1 (CPU) · transformers 5.19.0.
- **Corpus D.** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, sha256 `1d58a0fa…92669`; `page.get_text()` per page joined with `"\n"`; snapshot `ea07572562ac` (06 §5.3 recipe, executed from 06).
- **Index (= C2/C3/C4).** 07 H.1/H.3 recursive chunker, per page, 1000/200 → **97 chunks**; course ids `climate:ea07572562ac:1ca9c5a3b548:<seq:05d>`; `chunks.jsonl` sha256 `d4108b89…aadb3011b` (equal to the C2 lab's file: True). MiniLM `all-MiniLM-L6-v2`, normalised, float32, `V` (97, 384).
- **BM25.** `rank_bm25` 0.2.2 `BM25Okapi` (k1 1.5, b 0.75, epsilon 0.25) over P3's `tok_norm` (avgdl 111.23, vocabulary 1,769); the repo's `split()` for comparison (avgdl 109.49, vocabulary 2,630). BM25 lists keep only scores > 0.
- **Fusion (reference, `r1_measure.py`).** Each retriever passes its top-50 (`N_LIST`, 06 v2.0 card) as a dict `{chunk_id: score}`; ties everywhere by the smaller `chunk_id`. `minmax`: constant list → 1.0. `zscore3`: (s − (mean − 3·sd)) / (6·sd), population sd, not clipped, constant list → 0.5. `weighted`: each list normalised on its own; a missing id gets 0 (book Ch12 p.9/14). `rrf`: Σ 1/(k + rank), ranks from 1, k = 60.
- **Gold.** The 10 draft seeds parsed from 06 §6.7; relevance (`any_overlap`) and CE use `contracts_check.py`'s reference `rel` / `ce` (06 §7.2).
- **Not run.** No Groq or Cohere call; `.env` not read; no network. LangChain, FAISS and LlamaIndex are not installed: the repo's notebooks and script were **not run**; their logic was transcribed (S11).
- **Scripts** (this folder):

  | Script | Produces | Saved output |
  |---|---|---|
  | `r1_measure.py` | S1–S14 (and the `FP` lab fingerprints) | `out_r1_measure.txt` (run 1), `out_r1_measure_run2.txt` (run 2, byte-identical), `out_r1_measure.stderr.txt` (model-loading bar only) |
  | `r1_sources.py` | S-src: repo cells and lines, book pages and absences, the interview repo, course files | `out_r1_sources.txt` |
  | `r1_build_lab.py` | `labs/R1_hybrid_fusion_lab.ipynb` (no solution code; fingerprints read from `out_r1_measure.txt`) | — |
  | `r1_lab_runner.py` | runs the lab with a solutions file (no solution code) | — |
  | `r1_lab_solution.py` | the reference lab solution (coach-only, CR-04) | — |
  | `r1_lab_test.py` | LT: solution, alternative solution, blank, eight broken variants | `out_r1_lab_test.txt`, `out_r1_lab_good_full.txt` |
  | `r1_md_check.py` | MD: kit lint, item counts, Part A/L identity, links and anchors, word counts, 15-word book overlap, the snippet, key numbers | `out_r1_md_check.txt` |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/R1/r1_measure.py \
      "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/R1/out_r1_measure.txt 2> sources/verification/R1/out_r1_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/R1/r1_sources.py "$B" > sources/verification/R1/out_r1_sources.txt
  uv run python sources/verification/R1/r1_build_lab.py
  PYTHONIOENCODING=utf-8 uv run python sources/verification/R1/r1_lab_test.py > sources/verification/R1/out_r1_lab_test.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/R1/r1_md_check.py "$B" > sources/verification/R1/out_r1_md_check.txt
  ```
- **Determinism.** Two runs of `r1_measure.py` are byte-identical (diffed).
- **File hashes at the time of the final run** (sha256, first 8 hex): `r1_measure.py` `a2589041…`, `r1_sources.py` `d57f6ea0…`, `r1_build_lab.py` `e798afaf…`, `r1_lab_runner.py` `b97b4a78…`, `r1_lab_solution.py` `d1165ac8…`, `r1_lab_test.py` `2716388c…`, `r1_md_check.py` `875931e9…`, `labs/R1_hybrid_fusion_lab.ipynb` `02f3cb57…` (the notebook the lab test ran; rebuilding gives the same bytes), `study/questions/R1_questions.md` `6145ad33…`, `study/reading/R1_hybrid_fusion.md` `1abc5ec8…`. The full lesson's hash is not listed, because this file links to it and it changes with any edit.

## 1. Facts by section

`M` = `r1_measure.py`; `S` = `r1_sources.py`; `LT` = lab test; `MD` = `r1_md_check.py`.

### S1 Index and BM25

| Fact | Value | Source |
|---|---|---|
| Pages / characters / snapshot | 33 / 72,593 / `ea07572562ac` | M S1 |
| Chunks; `chunks.jsonl` sha256; = C2 lab file | 97; `d4108b89…`; True | M S1 |
| chunk_id string order = row order | True | M S1 |
| BM25 over `tok_norm` / `split()` | avgdl 111.23, vocab 1,769 / avgdl 109.49, vocab 2,630 | M S1 |

### S2 TOY: RRF by hand (O1-Q09 lists: dense [A, B, C], BM25 [C, A, D])

| Fact | Value | Source |
|---|---|---|
| k = 60 | A 0.032522 (123/3782), C 0.032266 (124/3843), B 0.016129 (1/62), D 0.015873 (1/63) → **A, C, B, D** | M S2 |
| Gaps | A − C 0.000256; C − B 0.016137; B − D 0.000256 | M S2 |
| k = 0, 1, 120 | same order A, C, B, D | M S2 |
| AIQ lists [0,1,2,3,4] + [4,1,3,2,0] | k = 60: [1, 0, 4, 2, 3] (1: 0.03226; 0 and 4: 0.03178; 2 and 3: 0.03150); k = 0: [0, 4, 1, 2, 3] (0 and 4: 1.2; 1: 1.0; 2 and 3: 0.58333) | M S2 |
| Consensus bound | 1/61 = 0.016393; 2/110 = 0.018182; 2/121 = 0.016529; 2/122 = 0.016393 | M S2 |
| Rank 1 vs rank 50 | 1/61 = 0.0164 vs 1/110 = 0.0091, ratio 1.803; k = 0: ratio 50 | M S2 |

### S3 TOY: normalisation and weighted fusion (dense A 0.62, B 0.58, C 0.41; BM25 C 7.9, A 2.1, D 1.8)

| Fact | Value | Source |
|---|---|---|
| min-max | dense A 1.0, B 0.8095, C 0.0; BM25 C 1.0, A 0.0492, D 0.0 | M S3 |
| weighted min-max | 0.5/0.5: A 0.5246, C 0.5000, B 0.4048, D 0 → A, C, B, D · 0.6/0.4: A 0.6197, B 0.4857, C 0.4000, D 0 → A, B, C, D · 0.7/0.3: A 0.7148, B 0.5667, C 0.3000 → A, B, C, D · 0.3/0.7: C 0.7000, A 0.3344, B 0.2429, D 0 → C, A, B, D | M S3 |
| three-sigma | dense A 0.6526, B 0.5793, C 0.2681; BM25 C 0.7355, A 0.3912, D 0.3734; 0.6/0.4: A 0.5480, C 0.4551, B 0.3476, D 0.1493 → A, C, B, D | M S3 |
| raw sum | C 8.31, A 2.72, D 1.80, B 0.58 → C, A, D, B | M S3 |
| rescaling | BM25 × 10 or √: raw-sum, min-max 0.6/0.4 and RRF orders unchanged; dense → exp(10 s): min-max dense B 0.6243, fused B 0.3746 < C 0.4000 → A, C, B, D (changed); RRF unchanged | M S3 |
| [2, 4, 6] | min-max [0, 0.5, 1]; three-sigma population [0.2959, 0.5, 0.7041]; sample [0.3333, 0.5, 0.6667] | M S3 |
| [1, 2, 3, 4, 100] | min-max [0, 0.0101, 0.0202, 0.0303, 1.0]; three-sigma population [0.4103, 0.4146, 0.4188, 0.4231, 0.8332]; sample [0.4198 … 0.798] | M S3 |
| Largest \|z\|, population sd, (n − 1)/√n | n = 2: 0.707; 5: 1.789; 10: 2.846; 11: 3.015; 50: 6.930; 97: 9.747 | M S3 |

### S4 The 10 draft seeds (draft-seed observations), k = 4

| Arm | Hit@4 | CE@4 | MRR@10 | First relevant rank D-001 … D-008 |
|---|---|---|---|---|
| dense | 8/8 | 8/8 | 0.708 | 3, 3, 1, 1, 1, 1, 2, 2 (= C4 fingerprint `a8aa456e76ccea3b`) |
| bm25 (`tok_norm`) | 8/8 | 8/8 | 0.938 | 1, 1, 1, 1, 1, 2, 1, 1 |
| bm25 (`split()`) | 8/8 | 8/8 | 0.875 | 1, 2, 1, 1, 1, 2, 1, 1 |
| rrf60 (top-50) | 8/8 | 8/8 | 1.000 | all 1 |
| mm 0.5/0.5 | 8/8 | 8/8 | 0.938 | 1, 1, 1, 1, 1, 2, 1, 1 |
| mm 0.6/0.4 | 8/8 | 8/8 | 0.938 | same |
| three-sigma 0.6/0.4 | 8/8 | 8/8 | 0.938 | same |

| Fact | Value | Source |
|---|---|---|
| Better / worse than dense (first relevant rank) | bm25, mm, z3: better D-001, D-002, D-007, D-008; worse D-006 · rrf60: better the same four; worse none | M S4 |
| First CE rank, D-007 | dense 3, bm25 2, rrf60 3, mm 0.5 2, mm 0.6 3 | M S4 |
| Dense and BM25 top-4 overlap (10 seeds) | [4, 4, 3, 3, 3, 3, 3, 1, 1, 2] = 27 of 40 | M S4 |
| BM25 lists (score > 0) | 80 to 97 chunks per seed | M S4 |

### S5 / S5b Walk-through seeds (draft-seed observations)

| Fact | Value | Source |
|---|---|---|
| D-008 tokens and idf | what, does, target: OOV (no chunk); `the`: n = 80, raw idf −1.5261, floored 0.8588; `kigali`, `amendment`: n = 1, idf 4.1641 | M S5 |
| D-008 dense top-4 | seq 28 page 10 0.2598 (no query token; "Carbon Pricing"); **seq 69 page 24 0.2535 (evidence)**; seq 58 page 20 0.2478; seq 12 page 5 0.2041 | M S5 |
| D-008 BM25 top-4 | **seq 69 9.4618**; seq 0 1.8858 (only "the"); seq 1 1.8377; seq 2 1.7458; gap ratio 5.02 | M S5, S5b |
| D-008 top-50 ranges | dense 0.2598 … 0.0909; BM25 9.4618 … 1.2000 | M S5b |
| D-008 normalised | seq 69: dense mm 0.9625, z3 0.9412; BM25 mm 1.0, z3 1.6546 · seq 28: dense mm 1.0 · seq 58: 0.9287 · seq 12: dense mm 0.6701, BM25 mm 0.0496 · seq 0: BM25 mm 0.0830 | M S5b |
| D-008 fused top-4 | raw sum: seq 69 9.71528, seq 0 1.88582, seq 7 1.87304, seq 27 1.84030 · mm 0.5/0.5: seq 69 0.98127, seq 28 0.50000, seq 58 0.46434, seq 12 0.35984 · mm 0.6/0.4: 0.97753, 0.60000, 0.55721, 0.42190 · z3 0.6/0.4: seq 69 1.22658, seq 12 0.63767, seq 56 0.62449, seq 83 0.61923 · RRF: seq 69 0.03252, seq 56 0.02885, seq 12 0.02845, seq 27 0.02840 | M S5b |
| D-008 RRF arithmetic | seq 69 = 1/62 + 1/61 = 0.016129 + 0.016393 = 0.032522; seq 56 = 1/66 + 1/73 = 0.028850 (DERIVED, = 0.02885 in M); seq 12 = 1/64 + 1/78 = 0.028446 (DERIVED, = 0.02845) | M S5b |
| D-008 dense rank-1 chunk (seq 28) | not in BM25 top-50; RRF 1/61 → fused rank 31; mm 0.5/0.5 → rank 2 | M S5, S5b |
| D-006 | seq 64 page 22 contains are, the, of, solar, panels, or (`panels` idf 4.1641); evidence seq 21 page 8 contains are, the, of, solar, on · dense seq 21 0.5331, seq 64 0.5004 · BM25 seq 64 13.6205, seq 21 9.2298 · mm 0.5/0.5: seq 64 first · RRF: seq 21 and seq 64 exactly equal (0.03252247488101534), smaller chunk_id first | M S5 |
| D-002 | dense evidence rank 3; BM25 rank 1 (15.4470); RRF seq 27 0.032266 vs seq 68 0.032258, margin 0.000008 | M S5 |

### S6 Demonstration: P3's five exact-term queries on the 97 chunks

| Query | Target (string) | dense | BM25 `tok_norm` | BM25 `split()` | RRF | mm 0.5 |
|---|---|---|---|---|---|---|
| `IPCC` | seq 1, page 1 | 3 | 1 | none | 1 | 1 |
| `What does BECCS stand for?` | seq 88, page 30 | 4 | 1 | none | 1 | 1 |
| `methane CH4` | seq 2, page 1 | 4 | 1 | 2 | 1 | 1 |
| `Kyoto Protocol 1997` | seq 69, page 24 | 1 | 1 | 1 | 1 | 1 |
| `limit warming to 1.5 degrees` | seq 27, 68 | 4 | 1 | 1 | 2 | 1 |
| D-002-P1 (06 §6.7 example paraphrase) | D-002 gold | 3 | 2 | — | 3 | 3 (CE@4 1 for all) |

### S7 RRF consensus rule (top-50 lists, k = 60)

Chunks in both lists per seed: 33, 26, 33, 29, 35, 28, 28, 30, 24, 37 (24–37); union 63–76. Every both-list chunk outranks every one-list chunk on **10/10** seeds (M S7).

### S8 Normalisation on the real lists

| Fact | Value | Source |
|---|---|---|
| Three-sigma values outside 0–1 (10 seeds × top-50) | dense 9/500, BM25 15/500 | M S8 |
| Best raw score per seed | dense 0.2598 … 0.7094; BM25 6.9559 … 43.6472 | M S8 |
| Unanswerable seeds, min-max top | D-009 dense 0.3099 → 1.0, BM25 6.9559 → 1.0; D-010 dense 0.5196 → 1.0, BM25 13.2576 → 1.0 | M S8 |

### S9 Rescaling one scorer (ordered top-4 changed, of 10 seeds)

| Change | raw sum | mm 0.5 | z3 0.5 | RRF |
|---|---|---|---|---|
| dense × 100 | 8 | 0 | 0 | 0 |
| BM25 × 10 | 3 | 0 | 0 | 0 |
| dense → exp(10 s) | 10 | 4 | 5 | 0 |
| BM25 → √s | 4 | 2 | 1 | 0 |

Raw sum: CE@4 8/8; its top-4 shares **37 of 40** chunks with the BM25 top-4 (M S9).

### S10 CR-08 probes

| Fact | Value | Source |
|---|---|---|
| k_rrf 0 / 1 / 10 / 60 / 120 / 1000 | top-4 changed vs k = 60: 5 / 5 / 3 / 0 / 1 / 1 of 10; CE@4 8/8 and MRR@10 1.000 throughout | M S10 |
| Dense weight 0.0 / 0.3 / 0.5 / 0.6 / 0.7 / 1.0 (min-max) | MRR@10 0.938 for 0.0–0.7 (first relevant ranks = BM25's); 0.708 at 1.0 (= dense) | M S10 |
| Weight 0.5 → 0.7 | ordered top-4 changed for 5/10 seeds; k_rrf 60 → 0: 5/10 | M S14 |
| Identity test | weight 1.0 top-4 = dense top-4 (10/10); weight 0.0 top-4 = BM25 top-4 (10/10) | M S10 |

### S11 The repo's fusion transcribed (cell 17 / script L75–L86), MiniLM in place of OpenAI

| Fact | Value | Source |
|---|---|---|
| Orders, first 5 rows | empty-string order [89, 50, 48, 49, 81]; query order (cell-19 query) [31, 7, 38, 30, 1] | M S11 |
| Normalised vector array | non-increasing by position (1.000 → 0.000): a ramp | M S11 |
| Cell-19 query, top-5 | repo-style rows [50, 28, 89, 48, 29]; aligned [1, 30, 37, 7, 0]; overlap 0/5 | M S11 |
| alpha = 1.0 | 1 distinct top-5 over 10 seeds = [89, 50, 48, 49, 81]; equals no seed's dense top-5 | M S11 |
| 8 answerable seeds, top-4, split() | repo-style Hit@4 0/8, CE@4 0/8; aligned 8/8, 8/8; repo-style with `tok_norm` 0/8 | M S11 |
| `IPCC` (all split() BM25 = 0) | script L81 without epsilon: NaN 97/97; repo-style (with epsilon) returns [89, 50, 48, 49, 81] (the empty-string order; the IPCC chunk not included); aligned returns the dense top-5 [85, 27, 1, 84, 69] | M S11 |
| TOY 3 documents (lab Task 4a) | vector by position [1.0, 0.5714, 0.0]; BM25 by row [1.0, 0.0, 0.3333]; combined [1.0, 0.2857, 0.1667]; repo order [d2, d0, d1]; aligned d0 0.5, d1 0.5, d2 0.4524 → [d0, d1, d2] | M S11 |

### S12–S13b Tokenizer, the LlamaIndex configuration, list depth

| Fact | Value | Source |
|---|---|---|
| RRF hybrid with `split()` BM25 / `tok_norm` | MRR@10 0.938 (D-002 rank 2) / 1.000; CE@4 8/8 both | M S12 |
| Three-sigma on two scores (any pair) | population sd 0.6667 / 0.3333; sample sd 0.6179 / 0.3821 | M S13 |
| List depth n = 2 / 4 / 10 / 20 / 50 / 97 | RRF MRR@10 0.875 / 1.000 / 1.000 / 1.000 / 1.000 / 1.000; min-max 0.875 / 0.938 …; CE@4 8/8 all; consensus rule broken on 1/10 seeds at n = 97 only | M S13b |

### S14 Lab fingerprints

37 `FP` lines in `out_r1_measure.txt`, read by `r1_build_lab.py`. Two reproduce C4: `seeds_first_rel_dense` = `a8aa456e76ccea3b` (C4 first_rel) and `lab_d002_dense_top4` = `78ebfed94d0021da` (C4 D-002 ids).

### S-src Citations (`r1_sources.py`: ALL PASS, 173 checks)

| Citation | Checked content |
|---|---|
| Repo HEADs | RAG_Techniques `009adba…`; AI-Engineer-Interview-Questions `e080df2…` |
| `fusion_retrieval.ipynb` cells 0, 10, 14, 15, 17, 19 | the design text; `FAISS.from_documents(cleaned_texts, …)`; BM25 over the same `cleaned_texts`; cell 17's ten key lines, including `similarity_search("", k=…ntotal)`, `similarity_search_with_score(query, k=len(all_docs))`, `+ epsilon`, `all_docs[i]`; no id alignment step; cell 19 `k=5, alpha=0.5` |
| `runnable_scripts/fusion_retrieval.py` | L40, L56, L61, L75, L76, L77, L79, L80, L81, L83, L84, L86, L100, L135; no epsilon in L75–L86 |
| `fusion_retrieval_with_llamaindex.ipynb` | cells 3, 8, 15, 17, 19 (0.6/0.4, `num_queries=1`, `dist_based_score`), 20 (the four modes; RRF called unsuitable for lack of normalisation; the mean ± 3 std formula), 22 |
| Repo-wide | RRF named only in llamaindex cell 20 (source cells and `.py` files) |
| Book, 47 page-phrase checks | Ch12 p.1–14/14; Ch13 p.5/13; App p.14, 16, 17, 19, 21/23 |
| Book absences | whole book: "reciprocal rank fusion", "RRF", "rank fusion", "Cormack", "z-score", "misalign": none · chapter 12: "reciprocal", rank-position wording, "clip", "alignment/aligned": none · "standard deviation" in chapter 12 only on p.8 |
| Interview repo | 04 Q9 and Q24 headings; Q24 code (`sorted(scores, key=scores.get, reverse=True)`), "Ranks are invariant to all of that.", "famously insensitive", the follow-ups; challenge 17 L131, L241, L245–L247; LICENSE (MIT, Copyright (c) 2026 Om) |
| Course files | O1 bank Q9 lists and key; session log O1-Q09 (confidence 3, score 2, A, C, B, D); review queue (R1 paused, 2026-10-17); the 02 R1 card (pages, cells, C#33); the 04 R1 row and DV-27; the 06 v2.0 card; P3 H.2; C4 fingerprints; MC-001…MC-006 |
| AE Ch2 'Retrieval Fundamentals' | the authors recommend keyword search as the first retrieval baseline (short-phrase check; paraphrased in the lesson) |

### LT Lab test (`out_r1_lab_test.txt`)

| Variant | CHECKs passed | Fails |
|---|---|---|
| good (reference solution) | **10/10** | — |
| good, alternative (literal 0.3 weight; different float expression in `rrf`) | **10/10** | — |
| blank | 0/10 | all |
| RRF ranks from 0 | 7/10 | Tasks 2, 6, 7 |
| no tie rule | 8/10 (9/10 in an earlier run) | Task 2, and Task 3 in some runs: with no tie rule, tied ids follow Python's set order, which depends on the per-process hash seed. The reference solution sorts by (−score, id) and is unaffected |
| min-max constant list → 0 | 9/10 | Task 3 |
| missing chunk → 0.5 | 6/10 | Tasks 3, 5, 7, 8 |
| three-sigma with sample sd | 9/10 | Task 3 |
| positional (misaligned) fusion | 4/10 | Tasks 3, 4a, 4b, 5, 7, 8 |
| `split()` BM25 | 7/10 | Tasks 5, 7, 8 |
| identity test too weak to catch the repo bug | 9/10 | Task 4b |

The good run also shows that the lab's given `rel`/`ce` helpers agree with `contracts_check.py` (same fingerprints as M).

### MD Document checks (`out_r1_md_check.txt`)

ALL PASS, 103 checks. Kit lint of the question file; 17 items (3 pre; 12 main: R 5, A 4, T 3; 2 interview); every reread line links into both files and names a book page; Part A and Part L ids and wording identical to the question file; every link and anchor resolves; the short file's snippet prints what its comment says; 97 key numbers found in `out_r1_measure.txt`; **no 15-word run shared with any book page** in any of the three Markdown files or the lab text (longest shared run: 7 words in the question and short files, under 6 in the full lesson and the lab); the interview excerpt (80 words) is verbatim from the MIT repo, with its notice. Word counts (whitespace-separated, as `wc -w`): short file 2,829 (2,410 without code blocks); full lesson 12,267 (11,202 without code blocks); question file 6,647.

## 2. Interface assumptions (for v2.0 and R3)

- Input: two result lists (dense from C4, BM25 from P3's tokenizer) over the **same** chunk ids, each with 1-based ranks and scores.
- Fusion joins on `chunk_id`, never on position; ties by `chunk_id`; a missing id adds 0 (weighted) or nothing (RRF).
- Output: the C4 record shape plus `source: "fused"` and `ranks_by_source` (06 §2.5); `score` is the fused value (for RRF, D-008 rank 1: 0.03252247488101534).
- Recorded with every run: k_rrf, list depth, weights, normaliser and its constant-list and clipping conventions, tokenizer and BM25 library version.

## 3. Corrections noted for other files (not edited)

1. **02 R1 card**: pages correct; misses Ch12 p.3–4, p.12–14/14 and the glossary pages.
2. **04 R1 row / DV-27**: the bug mixes **three** orders, not two (the returned documents come from the empty-string order); measured 0/8, not just "likely wrong".
3. **04 Ch12 table step 6**: the vector array is sorted by the query before normalising, so it becomes a ramp by position.
4. **P3 H.2 answer 4**: "vector-only" holds for aligned arrays; the repo's code returns the five chunks nearest to the empty string (S11).
5. **study/FORMAT.md** example anchor `#d3-bm25-exactly-as-rank_bm25-computes-it` does not match P3's real heading, which includes "0.2.2" (`#d3-bm25-exactly-as-rank_bm25-022-computes-it`).

## 4. UNVERIFIED

- LangChain FAISS ordering of `similarity_search("")`, whether OpenAI embeds an empty string, and FAISS returning squared L2 (our replication assumes squared L2; ranking is the same either way).
- LlamaIndex's `dist_based_score` code (sd convention, clipping, how duplicates are summed) and its legacy BM25 tokenizer.
- The Cormack et al. (2009) paper itself (only the formula is used; our code checks it).
- Any effect on the frozen eval set or Corpus T (v2.0, Part I: not run). Every seed number is a draft-seed observation.
