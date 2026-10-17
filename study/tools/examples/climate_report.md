# BM25 fit check

**What this is:** an automatic check of whether BM25 keyword search suits these documents and questions, measured on your own chunks.
**What this is not:** an evaluation. A few labelled questions show the mechanism; decide with many questions per type.

**Recommendation: use hybrid (BM25 + dense)** (section 6). Checklist: C1 ? C2 ✓ C3 ? C4 ✗ C5 ✓ C6 ✗ C7 ✗ C8 ✓ C9 ✗ C10 ✓ C11 ? C12 ?.

Settings: tokenizer `norm` · 1000-character chunks, overlap 200 · k 4 · k1 1.5, b 0.75, epsilon 0.25 · rank-bm25 0.2.2, numpy 2.5.3, pymupdf 1.26.7 · dense `sentence-transformers/all-MiniLM-L6-v2`.
Documents: `Understanding_Climate_Change.pdf` (33 page(s), 72,593 characters).

## 1 Collection

| Measure | Value | What it means |
|---|---|---|
| Chunks N | 91 | from 1 document(s) |
| Average length avgdl | 129.67 tokens | b compares each chunk with this |
| Vocabulary | 1,870 distinct tokens | |
| Mean idf (before the floor) | 3.352948 | |
| Floor = 0.25 × mean idf | 0.838237 | the idf used for any word in more than half of the chunks |
| Floored words | 18 (1.0% of the vocabulary) | `and`, `to`, `for`, `the`, `climate`, `in`, `of`, `are` … |
| The valley | n = 28 to 45 (14 words) | a word in 28 to 45 chunks is worth less than the most common words |
| Once-only tokens counted in 2+ chunks | 184 of 799 (23.0%) | the overlap doubles their df |
| Token fragments | 101 | word pieces cut at a chunk edge |

## 2 Tokenizer audit

20 distinct identifier-like strings, 62 occurrences: ALLCAPS 16, CamelCase 1, decimal 3. Chosen tokenizer: `norm`.
Flags: *punctuation attached* (`split()` glues brackets or commas to the name, so the bare name misses it), *case variants* (`split()` keeps case), *cut apart* (the whole name is not one token), *case split* (split where the letter case changes).

| Identifier | Class | Count | `split()` | `norm` | `code` | Flags |
|---|---|---|---|---|---|---|
| `CO2` | ALLCAPS | 23 | ✗ `CO2` · `CO2.` · `CO2,` · `(CO2),` | `co2` | `co2` | split: punctuation attached: `(CO2),` ×1, `CO2.` ×2, `CO2,` ×2; bare ×18 |
| `DAC` | ALLCAPS | 5 | ✗ `DAC` · `(DAC)` | `dac` | `dac` | split: punctuation attached: `(DAC)` ×2; bare ×3 |
| `AI` | ALLCAPS | 4 | ✗ `AI` · `(AI)` · `AI-driven` | `ai` | `ai` | split: punctuation attached: `(AI)` ×1, `AI-driven` ×1; bare ×2 |
| `CCS` | ALLCAPS | 4 | ✗ `(CCS)` · `CCS` | `ccs` | `ccs` | split: punctuation attached: `(CCS)` ×2; bare ×2 |
| `UNFCCC` | ALLCAPS | 4 | ✗ `UNFCCC` · `(UNFCCC)` · `(UNFCCC).` | `unfccc` | `unfccc` | split: punctuation attached: `(UNFCCC)` ×1, `(UNFCCC).` ×1; bare ×2 |
| `COP` | ALLCAPS | 3 | ✗ `(COP)` · `COP` | `cop` | `cop` | split: punctuation attached: `(COP)` ×2; bare ×1 |
| `IoT` | CamelCase | 3 | ✗ `IoT` · `(IoT)` | `iot` | `io` · `t` · `iot` | split: punctuation attached: `(IoT)` ×1; bare ×2 · code: case split, whole name kept |
| `GCF` | ALLCAPS | 2 | ✗ `(GCF)` · `GCF's` | `gcf` | `gcf` | split: punctuation attached: `(GCF)` ×1, `GCF's` ×1; the bare name never occurs |
| `2.2` | decimal | 1 | ✗ `(2.2` | `2.2` | `2.2` | split: punctuation attached: `(2.2` ×1; the bare name never occurs |
| `BECCS` | ALLCAPS | 1 | ✗ `(BECCS),` | `beccs` | `beccs` | split: punctuation attached: `(BECCS),` ×1; the bare name never occurs |
| `CH4` | ALLCAPS | 1 | ✗ `(CH4),` | `ch4` | `ch4` | split: punctuation attached: `(CH4),` ×1; the bare name never occurs |
| `CSR` | ALLCAPS | 1 | ✗ `(CSR)` | `csr` | `csr` | split: punctuation attached: `(CSR)` ×1; the bare name never occurs |
| `ESG` | ALLCAPS | 1 | ✗ `(ESG)` | `esg` | `esg` | split: punctuation attached: `(ESG)` ×1; the bare name never occurs |
| `GPS` | ALLCAPS | 1 | ✗ `GPS-guided` | `gps` | `gps` | split: punctuation attached: `GPS-guided` ×1; the bare name never occurs |
| `IPCC` | ALLCAPS | 1 | ✗ `(IPCC)` | `ipcc` | `ipcc` | split: punctuation attached: `(IPCC)` ×1; the bare name never occurs |
| `N2O` | ALLCAPS | 1 | ✗ `(N2O),` | `n2o` | `n2` · `o` · `n2o` | split: punctuation attached: `(N2O),` ×1; the bare name never occurs · code: case split, whole name kept |
| `WHO` | ALLCAPS | 1 | ✗ `(WHO),` | `who` | `who` | split: punctuation attached: `(WHO),` ×1; the bare name never occurs; case variants: `who` ×1, `WHO` ×1 |
| `1.5` | decimal | 2 | `1.5` | `1.5` | `1.5` | - |
| `EV` | ALLCAPS | 2 | `EV` | `ev` | `ev` | - |
| `1.2` | decimal | 1 | `1.2` | `1.2` | `1.2` | - |

`split()` column: the forms the name takes in the text after splitting at spaces. ✗ = does not survive whole.

## 3 Per question

| Question | Type | Chunks > 0 | Top score | Score at rank 4 | Right chunk's score |
|---|---|---|---|---|---|
| IPCC | exact-term | 1 | 3.8928 | - | 3.8928 |
| BECCS | exact-term | 80 | 5.0623 | 1.6156 | 5.0623 |
| CH4 | exact-term | 5 | 6.2813 | 2.6076 | 6.2813 |
| Kyoto | exact-term | 5 | 13.2706 | 5.4666 | 13.2706 |
| 1.5C | exact-term | 87 | 15.2079 | 7.7855 | 15.2079 |
| D-006 | paraphrase | 90 | 12.2375 | 10.0950 | 9.1425 |
| vague | other | 81 | 5.7608 | 4.4888 | - |

### IPCC · "IPCC"

- Tokens (`norm`): `ipcc`
- Not in the index (df 0, add nothing): (none)
- Rarest token: `ipcc`, idf 4.099885
- **Short list:** only 1 chunk(s) score above 0; returning 4 would pad with arbitrary chunks.

| Rank | Chunk | Page | Score | Matched tokens (count) |
|---|---|---|---|---|
| 1 | #1 | 1 | 3.8928 | `ipcc` ×1 |

Common words give 0% of the top score; 0 of the 1 matching chunks match through common words only.

### BECCS · "What does BECCS stand for?"

- Tokens (`norm`): `what` · `does` · `beccs` · `stand` · `for`
- Not in the index (df 0, add nothing): `what` · `does` · `stand`
- Rarest token: `beccs`, idf 3.577948; common tokens: `for`

| Rank | Chunk | Page | Score | Matched tokens (count) |
|---|---|---|---|---|
| 1 | #83 | 30 | 5.0623 | `beccs` ×1, `for` ×3 |
| 2 | #82 | 30 | 4.8803 | `beccs` ×1, `for` ×2 |
| 3 | #16 | 6 | 1.6720 | `for` ×6 |
| 4 | #53 | 19 | 1.6156 | `for` ×5 |

Common words give 28% of the top score; 78 of the 80 matching chunks match through common words only.

### CH4 · "methane CH4"

- Tokens (`norm`): `methane` · `ch4`
- Not in the index (df 0, add nothing): (none)
- Rarest token: `ch4`, idf 4.099885

| Rank | Chunk | Page | Score | Matched tokens (count) |
|---|---|---|---|---|
| 1 | #2 | 1 | 6.2813 | `methane` ×1, `ch4` ×1 |
| 2 | #5 | 2 | 4.9066 | `methane` ×4 |
| 3 | #6 | 2 | 4.5370 | `methane` ×3 |
| 4 | #4 | 2 | 2.6076 | `methane` ×1 |

Common words give 0% of the top score; 0 of the 5 matching chunks match through common words only.

### Kyoto · "Kyoto Protocol 1997"

- Tokens (`norm`): `kyoto` · `protocol` · `1997`
- Not in the index (df 0, add nothing): (none)
- Rarest token: `1997`, idf 4.099885

| Rank | Chunk | Page | Score | Matched tokens (count) |
|---|---|---|---|---|
| 1 | #64 | 23 | 13.2706 | `kyoto` ×2, `protocol` ×6, `1997` ×1 |
| 2 | #17 | 6 | 5.5429 | `kyoto` ×1, `protocol` ×1 |
| 3 | #25 | 9 | 5.5236 | `kyoto` ×1, `protocol` ×1 |
| 4 | #16 | 6 | 5.4666 | `kyoto` ×1, `protocol` ×1 |

Common words give 0% of the top score; 0 of the 5 matching chunks match through common words only.

### 1.5C · "limit warming to 1.5 degrees"

- Tokens (`norm`): `limit` · `warming` · `to` · `1.5` · `degrees`
- Not in the index (df 0, add nothing): (none)
- Rarest token: `1.5`, idf 3.230240; common tokens: `to`

| Rank | Chunk | Page | Score | Matched tokens (count) |
|---|---|---|---|---|
| 1 | #63 | 23 | 15.2079 | `limit` ×2, `warming` ×1, `to` ×5, `1.5` ×1, `degrees` ×2 |
| 2 | #26 | 10 | 15.1944 | `limit` ×2, `warming` ×1, `to` ×6, `1.5` ×1, `degrees` ×2 |
| 3 | #16 | 6 | 9.4237 | `limit` ×1, `warming` ×1, `to` ×2, `degrees` ×1 |
| 4 | #7 | 3 | 7.7855 | `warming` ×1, `to` ×4, `degrees` ×2 |

Common words give 10% of the top score; 79 of the 87 matching chunks match through common words only.

### D-006 · "What are the advantages of putting solar panels on lakes or reservoirs?"

- Tokens (`norm`): `what` · `are` · `the` · `advantages` · `of` · `putting` · `solar` · `panels` · `on` · `lakes` · `or` · `reservoirs`
- Not in the index (df 0, add nothing): `what` · `advantages` · `putting`
- Rarest token: `lakes`, idf 4.099885; common tokens: `are` · `the` · `of` · `on` · `or`

| Rank | Chunk | Page | Score | Matched tokens (count) |
|---|---|---|---|---|
| 1 | #59 | 22 | 12.2375 | `are` ×3, `the` ×6, `of` ×5, `solar` ×3, `panels` ×1, `on` ×1 |
| 2 | #60 | 22 | 12.0851 | `are` ×6, `the` ×5, `of` ×2, `solar` ×1, `panels` ×1, `or` ×1 |
| 3 | #12 | 5 | 11.8298 | `are` ×2, `the` ×7, `of` ×3, `solar` ×4, `on` ×1, `or` ×2 |
| 4 | #13 | 5 | 10.0950 | `are` ×1, `the` ×4, `of` ×2, `solar` ×4, `on` ×1, `or` ×1 |

Common words give 45% of the top score; 77 of the 90 matching chunks match through common words only.

### vague · "What can be done about this?"

- Tokens (`norm`): `what` · `can` · `be` · `done` · `about` · `this`
- Not in the index (df 0, add nothing): `what` · `done`
- Rarest token: `be`, idf 2.284780; common tokens: `can` · `be` · `about` · `this`
- **Vague warning:** every matched token is common (`can` · `be` · `about` · `this`), so the ranking rests on common words: 81 chunks match, none through a rare word.

| Rank | Chunk | Page | Score | Matched tokens (count) |
|---|---|---|---|---|
| 1 | #28 | 10 | 5.7608 | `can` ×2, `be` ×1, `about` ×1 |
| 2 | #22 | 8 | 5.4779 | `can` ×2, `be` ×2, `this` ×2 |
| 3 | #14 | 5 | 5.1387 | `can` ×4, `be` ×1, `this` ×2 |
| 4 | #46 | 17 | 4.4888 | `can` ×3, `about` ×1, `this` ×1 |

Common words give 100% of the top score; 81 of the 81 matching chunks match through common words only.

## 4 Measuring

Rank of the first chunk that contains the `expect` text (case and spacing ignored). BM25 ranks only chunks that score above 0; *not found* = the right chunk scores 0. Dense ranks every chunk.

| Question | Type | Right chunk(s) | `split()` | `norm` | `code` | Dense |
|---|---|---|---|---|---|---|
| IPCC | exact-term | #1 | not found | 1 | 1 | 3 |
| BECCS | exact-term | #82, #83 | not found | 1 | 1 | 3 |
| CH4 | exact-term | #2 | 3 | 1 | 1 | 2 |
| Kyoto | exact-term | #64 | 1 | 1 | 1 | 1 |
| 1.5C | exact-term | #26, #63, #64 | 1 | 1 | 1 | 3 |
| D-006 | paraphrase | #20 | 3 | 5 | 5 | 1 |

Per type, chosen tokenizer `norm` and dense (MRR = mean of 1 ÷ rank, not found = 0; no cut-off):

| Type | n | BM25 Hit@1 | BM25 Hit@4 | BM25 MRR | Dense Hit@1 | Dense Hit@4 | Dense MRR |
|---|---|---|---|---|---|---|---|
| exact-term | 5 | 5/5 | 5/5 | 1.000 | 1/5 | 5/5 | 0.500 |
| paraphrase | 1 | 0/1 | 0/1 | 0.200 | 1/1 | 1/1 | 1.000 |
| all | 6 | 5/6 | 5/6 | 0.867 | 2/6 | 6/6 | 0.583 |

BM25 MRR per type under each tokenizer:

| Tokenizer | exact-term | paraphrase | all |
|---|---|---|---|
| `norm` | 1.000 | 0.200 | 0.867 |
| `split` | 0.467 | 0.333 | 0.444 |
| `code` | 1.000 | 0.200 | 0.867 |

## 5 Checklist

✓ = no problem found · ✗ = a problem found on your data · ? = check by hand (the evidence helps).

| # | Check | Verdict | Evidence |
|---|---|---|---|
| C1 | Users search exact identifiers (codes, names, versions, numbers) | ? | manual: only you know what users type. Your documents contain 20 distinct identifier-like strings (62 occurrences): ALLCAPS 16, CamelCase 1, decimal 3. If users search for these, BM25 is the retriever that can match them exactly. |
| C2 | Identifiers survive the tokenizer | ✓ | under `norm`, all 20 identifiers stay whole. Measured on your exact-term questions, MRR: norm 1.000, split 0.467, code 1.000. |
| C3 | The same tokenizer is used for documents and questions | ? | manual: this tool uses `norm` on both sides. Check your own index and query code; a different tokenizer on one side means a token can never match. |
| C4 | Users also ask in their own words (paraphrases) | ✗ | measured on 1 paraphrase question(s): BM25 Hit@4 0/1, MRR 0.200; dense Hit@4 1/1, MRR 1.000. BM25 has no synonyms: a paraphrase only matches through shared words. |
| C5 | The collection is large and varied enough (≥ 3 chunks, mean idf > 0, floor > 0) | ✓ | 91 chunks, mean idf 3.352948, floor 0.838237; 1.0% of the vocabulary is floored. |
| C6 | Common words do not decide the ranking | ✗ | vague: 100% of the top score from common words (vague: no rare word matched). Chunks matched by common words only: up to 100% of a question's matches. |
| C7 | Only chunks with score > 0 are returned | ✗ | on your data the filter matters: IPCC has 1 chunk(s) above 0. Make sure your code drops scores ≤ 0 instead of always returning k. |
| C8 | Labelled questions exist | ✓ | 6 labelled (exact-term 5, paraphrase 1). Few questions per type: a demonstration, not an evaluation. |
| C9 | BM25 vs dense, per question type | ✗ | exact-term: BM25 MRR 1.000 vs dense 0.500; paraphrase: BM25 MRR 0.200 vs dense 1.000. Dense does better on: paraphrase. |
| C10 | k1 and b stay at their defaults unless measured | ✓ | k1 1.5, b 0.75, epsilon 0.25 (rank_bm25 0.2.2). |
| C11 | The chunking is fixed and recorded | ? | manual: record it with the index: 1000-character windows, 200 overlap, 91 chunks. The overlap counts 184 of 799 once-only tokens (23.0%) in two chunks, and 101 tokens are word pieces cut at a chunk edge. Any change alters every df and idf. |
| C12 | No fixed threshold on raw scores | ? | manual: top scores across your questions range 3.8928 to 15.2079; see the score table in section 3. A score depends on the question's words, not on whether a chunk answers it. |

## 6 Recommendation

**use hybrid (BM25 + dense)**

- exact-term: BM25 MRR 1.000 vs dense 0.500; paraphrase: BM25 MRR 0.200 vs dense 1.000. Dense does better on: paraphrase.
- measured on 1 paraphrase question(s): BM25 Hit@4 0/1, MRR 0.200; dense Hit@4 1/1, MRR 1.000. BM25 has no synonyms: a paraphrase only matches through shared words.
- vague: 100% of the top score from common words (vague: no rare word matched). Chunks matched by common words only: up to 100% of a question's matches.
