# P3_FACTS — what the P3 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/P3_bm25.md`](../../../concepts/P3_bm25.md) is listed here with the command and output section that produced it. Numbers that were not produced by these runs are marked DERIVED (arithmetic shown in the lesson) or UNVERIFIED.

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
  | `p3_sources.py` | S-src: checks every cited repo cell (0-based), repo line and book page | `out_p3_sources.txt` |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_measure.py "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/P3/out_p3_measure.txt 2> sources/verification/P3/out_p3_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P3/p3_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" \
      > sources/verification/P3/out_p3_sources.txt
  ```
- **Determinism.** Two consecutive runs of `p3_measure.py` gave byte-identical stdout (checked after the last edit with `diff`).

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

`p3_sources.py`: **ALL PASS**, 67 checks (repo HEAD `009adba2…`).

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

## 2. The lab: `labs/P3_bm25_lab.ipynb`

- Built by a generator script kept **outside** the workspace (session scratchpad, `p3/build_lab.py`). It computed the CHECK fingerprints from a reference implementation; the notebook holds only fingerprints, never the reference code.
- Tested with a **throwaway solution** kept outside the workspace (scratchpad `p3/test_lab.py`). Every cell ran in a real Jupyter kernel (`jupyter_client` + the project `ipykernel`):
  - good solution: **7/7 CHECK cells pass**;
  - broken solution, one planted bug per task (no lower-casing; textbook idf; floor at 0 instead of epsilon × mean; dl/avgdl inverted; k1 halved instead of doubled; zero score counted as a rank; the repo's `argsort` without a > 0 filter): **0/7 pass**, each CHECK failing on its own task's bug.
- The fingerprinted Task 6 ranks equal S9 (`IPCC` [None, 1], BECCS [None, 1], `methane CH4` [3, 1], Kyoto [1, 1], `1.5` [1, 1]).

## 3. DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| ln(1.8), 1.5 × 1.075, 5 / 3.6125, and 0.813546 + 2 × 0.562475 = 1.938496 (Part F); `eu` tf part 2.5 / 2.6125 = 0.956938; `emissions` in d5: K 0.9375, tf part 1.290323; 2,630 − 1,769 ≈ 860; five mentions = 1.92 × one | DERIVED in the lesson; every final value is printed in S4/S5/S9 |
| How dense retrieval ranks the same queries on our corpus | UNVERIFIED (R1) |
| LlamaIndex legacy `BM25Retriever` tokenizer | UNVERIFIED (not installed) |
| Porter / Snowball stemming behaviour | UNVERIFIED (not installed) |
| Lucene's or other libraries' IDF variants | UNVERIFIED |
| The runnable script's NaN | Formula replicated on our scores; the script was not run (it needs OpenAI) |

## 4. Notes for 04 and 02 (not edited; recorded here)

- **04 P3 row:** (1) the query-side `split()` is in `fusion_retrieval.ipynb` cell 17 (and `helper_functions.py` L262), not only cells 14–15; (2) the book column omits App p.14, 17, 18, 22/23, Ch12 p.8/14 and p.10/14; (3) `fusion_retrieval_with_llamaindex.ipynb` cell 15 is LlamaIndex's legacy `BM25Retriever`, a different implementation from `rank_bm25` + `split()`; (4) the default epsilon floor matters on real chunks (18 floored terms, S10). "TF-IDF not in book" is correct.
- **02 P3 card:** verified as written (`helper_functions.py:L248-L273`, whitespace split, no lower-casing, never called; cell 14; App pages). The card lists only P2 as a prerequisite; 03 also draws P1 → P3.
