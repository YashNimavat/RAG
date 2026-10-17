# P3_FACTS — what the P3 lesson can rely on (run-verified)

Run dates: **2026-10-08** (S1–S10, S-src) and **2026-10-17** (K1–K10, the extended S-src, MD). Every number in [`concepts/P3_bm25.md`](../../../concepts/P3_bm25.md), [`study/reading/P3_bm25.md`](../../../study/reading/P3_bm25.md) and [`study/questions/P3_questions.md`](../../../study/questions/P3_questions.md) is listed here with the command and output section that produced it, or comes from R1's run on the 97 chunks (§1b). Numbers that were not produced by these runs are marked DERIVED (arithmetic shown in the lesson) or UNVERIFIED.

**Two chunkings.** *91 windows* = P3's plain 1,000/200-character slices (S9, S10, K1–K3, K7, K8, the P3 lab; K4–K6, K9 and K10 are toys). *97 chunks* = the C-lab index (07 recursive chunker, per page), measured by R1 ([R1_FACTS](../R1/R1_FACTS.md)). The lessons label every number with its chunk set and never mix the two in one table without labels.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`).
- **Versions** (printed in S1): rank-bm25 0.2.2 · numpy 2.5.3 · pymupdf 1.26.7 · scikit-learn 1.9.1.
- **Corpus.** `C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques\data\Understanding_Climate_Change.pdf`, SHA-256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669` (repo pinned at `009adba`). Extraction as in the acceptance suite and P1: `page.get_text()`, pages joined with `"\n"`; 33 pages, 72,593 characters.
- **Windows.** Plain fixed character slices, size 1,000, overlap 200 (as P1 S4): 91 windows. Not LangChain's recursive splitter.
- **Toy corpus.** Six made-up sentences in `p3_measure.py` (S3). Toy illustration only.
- **No API calls.** No Groq or Cohere call; `.env` is never read; no network.
- **Scripts** (this folder):

  | Script | What it produces | Saved output |
  |---|---|---|
  | `p3_measure.py` | S1–S10: library formula facts, toy corpus, hand computation, saturation and b tables, IDF quirks, TF-IDF, tokenization, climate-PDF demonstration, NumPy vs `rank_bm25`. Also the reference solution of the lab (`bm25_numpy`, `tok_norm`). | `out_p3_measure.txt` (stdout), `out_p3_measure.stderr.txt` (stderr, empty) |
  | `p3_sources.py` | S-src: checks every cited repo cell (0-based), repo line and book page; since 2026-10-17 also the interview repo, AE Ch2, the R1_FACTS rows and the 02/04 claims used | `out_p3_sources.txt` |
  | `p3_kit_measure.py` (2026-10-17) | K1–K10: the BECCS walk-through, IPCC, the TF-IDF flip, the AIQ Q12 checks, code identifiers, a common-word query, overlap and fragments, two-document corpora, the steps of P3-A-01 and P3-A-05. `p3_measure.py` is left unchanged, so its output stays byte-identical | `out_p3_kit_measure.txt`, `out_p3_kit_measure.stderr.txt` (empty) |
  | `p3_md_check.py` (2026-10-17) | MD: kit lint, item counts, Part A/L identity, links and anchors (also links from other files into P3), strings other checkers rely on, the lab's task numbers, word counts, beats, 15-word book overlap, the snippet, every 3-decimal number against the outputs | `out_p3_md_check.txt` |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_measure.py "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/P3/out_p3_measure.txt 2> sources/verification/P3/out_p3_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" \
      > sources/verification/P3/out_p3_sources.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_kit_measure.py "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/P3/out_p3_kit_measure.txt 2> sources/verification/P3/out_p3_kit_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_md_check.py "$B" > sources/verification/P3/out_p3_md_check.txt
  ```
- **Determinism.** Two consecutive runs of `p3_measure.py` gave byte-identical stdout (checked after the last edit with `diff`). On 2026-10-17 it was re-run: stdout byte-identical to the saved 2026-10-08 file (`cmp`; sha256 `3091182068dcd6f0…` both), stderr empty. Two runs of `p3_kit_measure.py` are byte-identical too.
- **File hashes at the final run of 2026-10-17** (sha256, first 8 hex): `p3_measure.py` `10741bb8…`, `p3_kit_measure.py` `be0b93ba…`, `p3_sources.py` `47bac666…`, `p3_md_check.py` `42da7b24…`, `labs/P3_bm25_lab.ipynb` `ff3fd0f9…` (not changed on 2026-10-17), `study/questions/P3_questions.md` `6818e6f1…`, `study/reading/P3_bm25.md` `ae8d4fe4…`. The full lesson's hash is not listed, because this file links to it and it changes with any edit.

## 1. Facts by section

`M` = `p3_measure.py` (section in `out_p3_measure.txt`); `S` = `p3_sources.py`.

### S1 Environment

| Fact | Value | Source |
|---|---|---|
| Versions | rank-bm25 0.2.2, numpy 2.5.3, pymupdf 1.26.7, scikit-learn 1.9.1, Python 3.12.8 | M S1 |
| PDF pages / characters | 33 / 72,593 | M S1 |

### S2 `rank_bm25` 0.2.2 `BM25Okapi`, read from the installed source

| Fact | Value | Source |
|---|---|---|
| Signature | `(corpus, tokenizer=None, k1=1.5, b=0.75, epsilon=0.25)` | M S2 |
| IDF | `math.log(N - n + 0.5) - math.log(n + 0.5)` | M S2 (source line present) |
| Floor | `if idf < 0` → `epsilon * average_idf`; `average_idf` = mean over all terms before flooring | M S2 |
| Score | `idf * f*(k1+1) / (f + k1*(1 - b + b*dl/avgdl))`, looped over the query list; unknown term → 0 | M S2 |
| dl, avgdl | `len(document)` (repeats counted); total tokens / number of docs | M S2 |
| `tokenizer=` argument | uses a `multiprocessing.Pool` (not used in the lesson) | M S2 |

### S3 Toy corpus (`tok_norm`)

| Fact | Value | Source |
|---|---|---|
| Doc lengths d0–d5 | 11, 10, 13, 11, 10, 5; total 60; avgdl 10.0; vocabulary 44 | M S3 |
| Mean IDF before floor / floor | 1.089767 / 0.272442 | M S3 |
| idf `bpa`, `regulation`, `2019`, `emissions` (n = 2) | 0.587787 | M S3 |
| idf `eu` (n = 1) | 1.299283 | M S3 |
| idf `plastics`, `the` (n = 3) | 0.000000 | M S3 |
| `climate`, `and` (n = 4) | raw −0.587787 → floored 0.272442 | M S3 |

### S4 Hand computation and single-term scores

| Fact | Value | Source |
|---|---|---|
| `bpa` in d0: N, n, f, dl, avgdl | 6, 2, 2, 11, 10.0 | M S4 |
| idf / K / tf part / score | 0.587787 / 1.612500 / 1.384083 / **0.813546**; rank_bm25 0.813546; diff 0.0e+00 | M S4 |
| Query `bpa regulation 2019`, scores d0–d5 | 1.938496, 0.587787, 1.28372, 0, 0, 0 (NumPy reference identical, max diff 0.0) | M S4 |
| d0 contributions `regulation`, `2019` | 0.562475 each | M S4 |
| `bpa` in d2 (f 2, dl 13) | 0.765846 | M S4 |
| `2019` in d2 | 0.517874 | M S4 |
| `eu` in d0 | **1.243333** | M S4 |
| `regulation` in d1 | 0.587787 | M S4 |
| `emissions` in d5 (dl 5) / in d4 (dl 10) | 0.758434 / 0.587787 | M S4 |

### S5 Saturation and length normalisation (tf part)

| Fact | Value | Source |
|---|---|---|
| tf part at dl = avgdl, f = 0, 1, 2, 3, 5, 10, 100, 1000 | 0, 1.0, 1.4286, 1.6667, 1.9231, 2.1739, 2.4631, 2.4963; limit 2.5 | M S5 |
| f = 1, b = 0.75, dl/avgdl = 0.5, 1, 2, 4 | 1.2903, 1.0, 0.6897, 0.4255 | M S5 |
| f = 1, dl = 2·avgdl, b = 0, 0.375, 0.75, 1 | 1.0, 0.8163, 0.6897, 0.625 | M S5 |
| f = 1, dl = 0.5·avgdl, b = 0, 0.375, 0.75, 1 | 1.0, 1.1268, 1.2903, 1.4286 | M S5 |
| k1 = 0, 0.75, 1.5, 3.0 at dl = avgdl, f = 1/2/5 | [1,1,1], [1, 1.2727, 1.5217], [1, 1.4286, 1.9231], [1, 1.6, 2.5] | M S5 |
| CR-08: k1 1.5 → 3.0 (f 2, dl = avgdl) | 1.4286 → 1.6 | M S5 |
| CR-08: b 0.75 → 0.375 (f 1, dl = 2·avgdl) | 0.6897 → 0.8163 | M S5 |
| rank_bm25 on a padded doc, score/idf at f = 1, 10, 100, 1000 | 1.000000, 2.173913, 2.463054, 2.496256 | M S5 |
| x once in a 20-token and a 5-token doc (avgdl 14.1667) | b = 0.75: 0.495899 vs 0.829243; b = 0: 0.587787 each | M S5 |

### S6 IDF and parameter quirks

| Fact | Value | Source |
|---|---|---|
| `plastics` (3 of 6) | idf 0, all scores 0 | M S6 |
| `climate` (4 of 6) scores | 0, 0.272442, 0, 0.26071, 0.272442, 0.351538 | M S6 |
| Two-document corpus | idf 0, scores [0.0, 0.0] | M S6 |
| Three docs `[a b c], [a b], [a b]` | raw idf a = −1.945910, c = 0.510826; mean −1.126998; floor −0.281750; scores for `a`: −0.249652, −0.301106, −0.301106 | M S6 |
| Repeated query term | `bpa` 0.813546 → `bpa bpa` 1.627091 | M S6 |
| Unknown term `ipcc` | all 0 | M S6 |
| k1 = 0, query `bpa` | [0.588, NaN, 0.588, NaN, NaN, NaN]; 1 numpy RuntimeWarning | M S6 |

### S7 TF-IDF and other tokenizers

| Fact | Value | Source |
|---|---|---|
| tf × ln 3 vs BM25 (`bpa`, dl = avgdl), f = 1, 2, 4, 8, 16 | 1.0986/0.5878, 2.1972/0.8397, 4.3944/1.0687, 8.7889/1.2374, 17.5778/1.3435 | M S7 |
| sklearn `TfidfVectorizer` defaults | lowercase True; token_pattern `(?u)\b\w\w+\b`; smooth_idf True; sublinear_tf False; norm l2 | M S7 |
| sklearn idf_ for `bpa` | 1.847298 = ln(7/3) + 1 | M S7 |
| Sample sentence under sklearn / `norm` / `split` / `\w+` | `1.5` and `a` dropped / kept / `degrees;`, `CO2,`, `(IPCC)` / `1`, `5` | M S7 |
| `Upgrade to v2.10.3 if you see ERR_CONN_RESET.` | `\w+`: `v2`,`10`,`3`,`err_conn_reset`; `norm`: `v2.10.3`,`err`,`conn`,`reset`; sklearn: `v2`,`10`,`err_conn_reset` (3 dropped) | M S7 |

### S8 Toy query under `split()`

| Fact | Value | Source |
|---|---|---|
| `split()` d0 tokens include | `BPA`, `(2019):`, `food-contact`, `plastics.` | M S8 |
| Scores for `BPA regulation 2019`: split / norm | [2.1246, 0, 1.6482, 0, 0, 0] / [1.9385, 0.5878, 1.2837, 0, 0, 0] | M S8 |
| split index, lower-case query | [1.2894, 0, 1.1348, 0, 0, 0] | M S8 |

### S9 Climate PDF demonstration (91 windows)

| Fact | Value | Source |
|---|---|---|
| Vocabulary: split / lower+split / lower+\w+ / norm / norm+fold | 2,630 / 2,276 / 1,767 / 1,769 / 1,617 | M S9 |
| `split()` spellings of "emissions" | `emissions` 22, `emissions.` 20, `emissions,` 7, `Emissions` 1 | M S9 |
| `split()` tokens containing IPCC / BECCS / CH4 | `(IPCC)` 1 / `(BECCS),` 1 / `(CH4),` 1 | M S9 |
| Toy fold | beccs → becc, emissions → emission, gases → gase, this → thi, ccs → ccs | M S9 |
| `IPCC` (target window 1) | split and lower+split: 0 windows > 0, not found; \w+, norm, fold: rank 1 | M S9 |
| `What does BECCS stand for?` (windows 82, 83) | split, lower+split: 0 windows > 0; others: rank 1 (80 windows > 0) | M S9 |
| `methane CH4` (window 2) | split: 3 windows > 0, rank 3; lower+split: rank 3; others rank 1 (5 windows > 0) | M S9 |
| `Kyoto Protocol 1997` (window 64) | rank 1 for all five (5 windows > 0) | M S9 |
| `limit warming to 1.5 degrees` (windows 26, 63, 64) | rank 1 for all five (87 windows > 0); \w+ query becomes `1`, `5` (in 5 and 4 windows) | M S9 |
| Repo-style top 5 for all-zero IPCC scores | [90, 89, 88, 87, 86] | M S9 |
| Min-max without epsilon (script L81 formula) / with 1e-8 (cell 17) | 91 of 91 NaN / all 0 | M S9 |

### S10 NumPy vs library; negative IDF on real windows

| Fact | Value | Source |
|---|---|---|
| max abs diff, 7 queries × 2 tokenizers × 91 windows | 1.1e-13 | M S10 |
| `norm`: vocabulary / avgdl / mean IDF / floor | 1,870 / 129.67 / 3.352948 / 0.838237 | M S10 |
| Terms in more than half of the windows (floored) | 18: and 91, to 87, the 80, for 80, climate 77, in 76, of 74, are 67, is 65, can 65, change 59, these 53, as 52, a 51, this 50, sustainable 50, such 49, action 49 | M S10 |
| idf `climate` (n 77) / `ipcc` (n 1) / `emissions` (n 34) | 0.838237 / 4.099885 / 0.510826 | M S10 |

### S-src Citations

`p3_sources.py`: **ALL PASS**, 67 checks on 2026-10-08 (repo HEAD `009adba2…`); **105 checks** after the 2026-10-17 additions (the last row of this table).

| Citation | Checked content |
|---|---|
| `fusion_retrieval.ipynb` cell 5 | `from rank_bm25 import BM25Okapi` |
| cell 10 | `chunk_size=1000, chunk_overlap=200` defaults; `RecursiveCharacterTextSplitter(`; `length_function=len`; `replace_t_with_space(texts)` |
| cell 14 | `create_bm25_index`; "improvement over TF-IDF"; whitespace comment; "could be improved with more sophisticated tokenization"; `doc.page_content.split()`; `BM25Okapi(tokenized_docs)`; no `.lower(` |
| cell 15 | `bm25 = create_bm25_index(cleaned_texts)` |
| cell 17 | `epsilon = 1e-8`; `bm25.get_scores(query.split())`; min-max with `+ epsilon`; `argsort(combined_scores)[::-1]` |
| cell 19 | the climate-impacts query; `k=5, alpha=0.5` |
| `fusion_retrieval_with_llamaindex.ipynb` cells 3, 15 | legacy `BM25Retriever` import; `BM25Retriever.from_defaults(`, `similarity_top_k=2` |
| `simple_rag.ipynb` cell 3 | `rank_bm25==0.2.2` |
| `helper_functions.py` | L9 import; L248 `def bm25_retrieval`; L262 `query.split()`; L265 `get_scores`; L268 `argsort(...)[::-1][:k]`; L273 `return top_k_texts`; the name occurs once in the whole repo (`.py`, `.ipynb`, `.md`): defined, never called |
| `all_rag_techniques_runnable_scripts/fusion_retrieval.py` | L56 `split()` index; L76 `query.split()`; L81 min-max without epsilon |
| Book | Ch12 p.1/14 (BPA query; ranks fourth), p.2/14, p.3/14 (index analogy), p.5/14 (Best Match 25; no embeddings; three factors; five mentions vs one; "scores almost nothing"; idf; length normalization), p.6/14 (query tokenized into words; Rarity), p.8/14 (unbounded scale), p.10/14 (tokenize each chunk; codes and citations), p.14/14; Ch13 p.5/13; App p.14/23, p.17/23, p.18/23, p.22/23. Each phrase < 15 words |
| Book absences | No `TF-IDF`, `k1`, `Okapi`, stemming, lower-casing, `saturat` or stop-word anywhere in the 25 PDFs |
| Added 2026-10-17 (38 checks) | Book: App p.9/23 (keyword search for exact method names), Ch12 p.2/14 (keyword search misses), p.3/14 (the index catches what the chef misses), p.9/14 (technical queries), p.12/14 ("Overkill when"; BM25 alone for all keyword lookups; vector alone for natural-language questions). AIQ HEAD `e080df2…`, LICENSE (MIT, Copyright (c) 2026 Om), Q12 heading and the answer lines quoted or corrected, and that Q12 gives no idf formula and no (k1 + 1). AE Ch2 'Retrieval Fundamentals' (keyword search first; short phrase, paraphrased). R1_FACTS: the five S6 rows, the three S4 rows, D-006 (S5), D-009/D-010 (S8), the S1 BM25 index, the S11 IPCC row, the P3 H.2 note. 06 §6.2 `exact-term` category and the §4.2 v2.0 three arms. The 02 P3 card's book pages and the 04 P3 row (G.3 items 1, 2, 5) |

## 1b. Added 2026-10-17: K1–K10 (`p3_kit_measure.py`) and the 97-chunk numbers used

`K` = `p3_kit_measure.py` (section in `out_p3_kit_measure.txt`). All K numbers are on the **91 windows** or a toy.

### K1 Environment

| Fact | Value | Source |
|---|---|---|
| Versions | rank-bm25 0.2.2, numpy 2.5.3, pymupdf 1.26.7, Python 3.12.8; PDF sha256 `1d58a0fa…92669` | K K1 |
| 91 windows, `tok_norm` | avgdl 129.6703; mean idf 3.352948; floor 0.838237 (= S10) | K K1 |

### K2 The running example: "What does BECCS stand for?" (91 windows)

| Fact | Value | Source |
|---|---|---|
| Query tokens | `tok_norm`: what, does, beccs, stand, for · `split()`: What, does, BECCS, stand, for? | K K2 |
| df / idf | what, does, stand: df 0 (not in the index, add 0) · beccs: df 2, idf 3.577948 · for: df 80, raw −1.945910 → floor 0.838237 | K K2 |
| Windows > 0 | 80 of 91; top 5: 83 5.0623, 82 4.8803, 16 1.672, 53 1.6156, 45 1.607 | K K2 |
| Window 83 (rank 1) | dl 124, K 1.450805; beccs f 1, tf part 1.020073 → 3.649768; for f 3, tf part 1.685088 → 1.412504; total 5.062271 | K K2 |
| Window 82 (rank 2) | dl 123, K 1.442129; beccs tf part 1.023697 → 3.662734; for f 2, tf part 1.452589 → 1.217614; total 4.880348 | K K2 |
| Window 16 (rank 3) | dl 132, K 1.520212; for f 6, tf part 1.994625 → 1.671968; ceiling for "for" idf × 2.5 = 2.095593 | K K2 |
| One mention, df 2 | "BECCS" occurs once, at character 66441; window 82 covers 65600–66600, window 83 66400–67400: both contain it | K K2 |
| `split()` | the text's token is `(BECCS),`; no `split()` query token occurs in any window | K K2 |

### K3–K10

| Fact | Value | Source |
|---|---|---|
| `IPCC` | df 1, idf 4.099885; window 1: f 1, dl 145, K 1.632998, tf part 0.949488, score 3.892792; `split()` token `(IPCC)` | K K3 |
| TOY: TF-IDF flip, query `bpa ban`, six 8-token docs | textbook TF-IDF x 2.8904, y 6.5917 (y first) · BM25 x 1.8871, y 1.1756 (x first); idf bpa 0.587787, ban 1.299283; tf part at f 6 = 2.000000 | K K4 |
| AIQ Q12 checks (dl = avgdl) | tf part f 1, 2, 20, 21: 1.0, 1.428571, 2.325581, 2.333333; gains 0.428571 and 0.007752; the repo's `f/(f + K)` form is the tf part ÷ 2.5 for every f | K K5 |
| TOY: code identifiers (P3-T-02), ten function signatures | `tok_norm`: `getUserId` → `getuserid` (one token), `get_user_id` → get, user, id; query "user id": 2 signatures > 0 (delete_user 2.6276, get_user_id 2.1134), getUserId not found; query "getUserId": getUserId 2.0176, the only match · parts only: "user id" → getUserId rank 2 (tied with get_user_id at 1.0983; delete_user 1.4243 first); "getUserId" → getUserId and get_user_id tie at 1.8392 · parts + whole name: "user id" → getUserId rank 2 (1.1126); "getUserId" → getUserId 3.6807, get_user_id 1.8631 | K K6 |
| A common-word question | "What can be done about this?": what, done not in the index; can (65) and this (50) floored 0.838237; be, about (8) 2.284780; 81 of 91 windows > 0; rank 1 5.7608, rank 5 4.3718, rank 10 3.6997, rank 40 1.7162 | K K7 |
| Overlap and fragments | 799 tokens occur once in the whole text; 184 of them (23.0%) are counted in 2 windows; window vocabulary 1,870 vs whole text 1,769: 101 window tokens are pieces cut at a window edge; 0 whole-text tokens missing | K K8 |
| Two-document corpora | words in one doc: idf 0, scores [0.0, 0.0]; a word in both: idf (floor) −0.080472, scores [−0.080472, −0.080472]. **Corrects** the 2026-10-08 lesson's "every score is 0" (D.3 detail 2, coach note) | K K9 |
| Steps of P3-A-01 / P3-A-05 | eu in d0: K 1.612500, tf part 0.956938, score 1.243333 · emissions in d5: K 0.937500, tf part 1.290323, score 0.758434 (both = rank_bm25). These were DERIVED on 2026-10-08 and are now printed | K K10 |

### Numbers taken from R1's run (97 chunks; not re-measured here)

| Fact | Value | Source |
|---|---|---|
| Five exact-term queries | dense rank 3, 4, 4, 1, 4; BM25 `tok_norm` 1, 1, 1, 1, 1; BM25 `split()` none, none, 2, 1, 1 (IPCC, BECCS, methane CH4, Kyoto 1997, 1.5 degrees) | R1_FACTS S6 |
| BM25 index on the 97 chunks | `tok_norm`: avgdl 111.23, vocabulary 1,769 | R1_FACTS S1 |
| 8 answerable draft seeds, k = 4 | dense Hit@4 8/8, CE@4 8/8, MRR@10 0.708; BM25 `tok_norm` 8/8, 8/8, 0.938; BM25 `split()` 8/8, 8/8, 0.875 | R1_FACTS S4 |
| D-006 (paraphrase) | BM25 seq 64 (page 22, "panels", idf 4.1641) 13.6205 above the evidence seq 21 9.2298; dense seq 21 first (0.5331) | R1_FACTS S5 |
| Unanswerable seeds | best BM25 D-009 6.9559, D-010 13.2576 | R1_FACTS S8 |
| The repo's fusion on `IPCC` | repo-style returns [89, 50, 48, 49, 81] (nearest to the empty string, IPCC chunk absent); the script's formula: NaN 97/97 | R1_FACTS S11 |

## 2. The lab: `labs/P3_bm25_lab.ipynb`

- Built by a generator script kept **outside** the workspace (session scratchpad, `p3/build_lab.py`). It computed the CHECK fingerprints from a reference implementation; the notebook holds only fingerprints, never the reference code.
- Tested with a **throwaway solution** kept outside the workspace (scratchpad `p3/test_lab.py`). Every cell ran in a real Jupyter kernel (`jupyter_client` + the project `ipykernel`):
  - good solution: **7/7 CHECK cells pass**;
  - broken solution, one planted bug per task (no lower-casing; textbook idf; floor at 0 instead of epsilon × mean; dl/avgdl inverted; k1 halved instead of doubled; zero score counted as a rank; the repo's `argsort` without a > 0 filter): **0/7 pass**, each CHECK failing on its own task's bug.
- The fingerprinted Task 6 ranks equal S9 (`IPCC` [None, 1], BECCS [None, 1], `methane CH4` [3, 1], Kyoto [1, 1], `1.5` [1, 1]).

## 3. DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| ln(1.8), 1.5 × 1.075, 5 / 3.6125, and 0.813546 + 2 × 0.562475 = 1.938496 (Part F); 2,630 − 1,769 ≈ 860; five mentions = 1.92 × one | DERIVED in the lesson; every final value is printed in S4/S5/S9 |
| `eu` tf part 2.5 / 2.6125 = 0.956938; `emissions` in d5: K 0.9375, tf part 1.290323 | DERIVED on 2026-10-08; **printed** since 2026-10-17 (K10) |
| The P3-A-03 steps (K = 2.625 and 2.0625; 2.5 / 3.625; 2.5 / 3.0625); 1 + K for P3-A-01 and P3-A-05; ln 6 = 1.792 (a wrong answer); "78 of the 80 windows" (80 − 2, D.3) | DERIVED in the text; listed in `p3_md_check.py` (DERIVED); every final value is printed in S5, K2 or K10 |
| How dense retrieval ranks the same queries | **Measured on the 97 chunks** by R1 (S6; §1b). On the 91 windows: UNVERIFIED |
| LlamaIndex legacy `BM25Retriever` tokenizer | UNVERIFIED (not installed) |
| Porter / Snowball stemming behaviour | UNVERIFIED (not installed) |
| Lucene's or other libraries' IDF variants | UNVERIFIED |
| The interview repo's "k1 typically ~1.2 to 2.0", "b typically ~0.75" | UNVERIFIED (no primary source checked) |
| "my screen goes dark" vs "the display turns off" (P3-T-03) | Made-up scenario; the "no shared word" point is read off the two sentences, not measured |
| The runnable script's NaN | Formula replicated on our scores; the script was not run (it needs OpenAI) |

## 4. Notes for 04 and 02 (not edited; recorded here)

- **04 P3 row:** (1) the query-side `split()` is in `fusion_retrieval.ipynb` cell 17 (and `helper_functions.py` L262), not only cells 14–15; (2) the book column omits App p.14, 17, 18, 22/23, Ch12 p.8/14, p.9–10/14 and p.12/14; (3) `fusion_retrieval_with_llamaindex.ipynb` cell 15 is LlamaIndex's legacy `BM25Retriever`, a different implementation from `rank_bm25` + `split()`; (4) the default epsilon floor matters on real chunks (18 floored terms, S10). "TF-IDF not in book" is correct. Re-checked 2026-10-17 (`p3_sources.py`): unchanged.
- **02 P3 card:** the repo lines verified as written (`helper_functions.py:L248-L273`, whitespace split, no lower-casing, never called; cell 14; App pages). The card lists only P2 as a prerequisite; 03 also draws P1 → P3. **Added 2026-10-17:** its book pages are correct but incomplete: only Ch12 p.5–6/14 and the glossary; missing Ch12 p.1–2/14 (the story its own "Failure" line describes), p.8/14, p.9–10/14, p.12/14 and p.14/14.
- **This lesson (2026-10-08 version), corrected on 2026-10-17:** (1) H.2 answer 4 said the repo's fusion becomes "vector-only" when every BM25 score is 0; with the repo's misaligned arrays it returns the five chunks nearest to the empty string (R1_FACTS S11 and §3 item 4 there). (2) D.3 detail 2 and its coach note said a two-document corpus gives "every score 0"; a word in both documents scores −0.080472 (K9).

## 5. MD Document checks (`out_p3_md_check.txt`)

ALL PASS, 129 checks (2026-10-17). Kit lint of the question file; 18 items (5 pre; 11 main: R 4, A 4, T 3; 1 review; 1 interview); the 2026-10-08 Part L ids kept; every reread line links into both the short and the full file and names a book page; Part A and Part L ids and wording identical to the question file; every link and anchor resolves, including the 7 links from other files (R1) into the P3 files; the strings `r1_sources.py` and `coach_sources.py` rely on are still in the full lesson; none of the coach seed bank's S2 words occurs in the three files; H.1 lists the lab's 7 tasks in order; the short file's snippet prints what its comments say; every number with 3 or more decimals in the three files matches a printed value or the DERIVED list; **no 15-word run shared with any book page** in the three Markdown files or the lab text (longest shared run: 7 words in the full lesson, under 6 in the question file, the short file and the lab). The interview excerpt (two paragraphs) is verbatim from the MIT repo, with its notice.

A second, separate overlap check (2026-10-17): the text of all 25 book PDFs was extracted into the session scratchpad, outside the repo, and compared with the short file, the question file, the full lesson and this file. Result: **0** shared 15-word runs; longest shared run 5, 6, 7 and 7 words respectively. The extracted text was then deleted. After P3-T-02 was rewritten, the check was repeated on the question file and the full lesson: 0 shared 15-word runs, longest 5 and 7 words; the extracted text was deleted again.

Word counts (whitespace-separated, as `wc -w`): short file 2,934 (2,309 without code blocks); full lesson 11,743 (11,136 without code blocks; 8,400 before the restyle); question file 6,801.

## 6. Revision log

- **2026-10-08.** S1–S10 and S-src (67 checks); the lesson and the lab.
- **2026-10-17.** Study kit and restyle. New: `study/reading/P3_bm25.md`, `study/questions/P3_questions.md`, `p3_kit_measure.py` (K1–K10), `p3_md_check.py` (MD). Extended: `p3_sources.py` (+38 checks). Restyled: `concepts/P3_bm25.md` (B–K in the house style; Parts A and L = the question file; R1's 97-chunk numbers brought in with labels; two corrections, §4). Unchanged: `p3_measure.py` and its output, the lab. Later the same day, P3-T-02 was rewritten as a code-identifier scenario (K6 replaced), at the coordinator's request; the coach files were not touched and `coach_sources.py` gives 182 PASS, 0 FAIL.
