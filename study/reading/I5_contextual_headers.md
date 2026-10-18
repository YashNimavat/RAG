<!-- kit:reading concept=I5 depth=short version=1 -->
# I5: Contextual chunk headers and contextual retrieval

**What this is:** the short reading for I5, the text version of the HTML lesson's Short depth ([`study/lessons/I5_contextual_headers.html`](../lessons/I5_contextual_headers.html)), in the lesson's 12 steps. One running example: the climate PDF (Corpus D), its 97 v0 chunks, and the near-duplicate draft questions D-002 and D-003. It answers every question in [`study/questions/I5_questions.md`](../questions/I5_questions.md).
**What this is not:** the Full depth (the upstream notebook cell by cell, late chunking, framework defaults), the BM25 side of headers (v2.0, R1), or headers shown to the generator.

**The answer first.**
1. A chunk cut out of a document can lose what it is about: its chapter, its section, the thing "it" refers to. A question that names the subject then has nothing to match.
2. A contextual header puts that context back at index time. You prepend a short description (a heading path, or a sentence an LLM wrote) to the text you **embed**. The stored chunk text and its offsets do not change.
3. A header helps only if it **differs between chunks**. On one PDF the document title is the same for all 97 chunks, so it carries nothing to rank by. Only the chapter and section levels separate the two "Paris Agreement" pages.
4. Which heading a chunk gets is a rule, and the rule matters. On chunk 68, the gold chunk of D-003, the heading in effect at the chunk's start names the wrong chapter. On chunk 34 the same rule is the one that gets it right.
5. The LLM version costs one call per chunk, each carrying the whole document: cheap only with prompt caching, and too big for Groq's free tier. Vendors report gains that about 50 questions cannot detect. So v1.2 measures the free heading-path header first, with CE@4.

> **Read in the book:** Ch7 p.1–2/11, then p.4–9/11. Read after §2. The pages come from the course plan (02, 04); the book was not open when this was written, so check them. Its "0.1 → 0.9" claim (p.8–9/11) was never measured (§12).

**Labels used below.** *Measured* numbers come from `i5_kit_measure.py` on Corpus D ([I5_FACTS](../../sources/verification/I5/I5_FACTS.md) K1–K15). *Derived* token counts are estimates from measured characters per token (6.21 for MiniLM's WordPiece, 5.65 for `o200k_harmony`): no tokenizer could be downloaded here. *Toy* means made-up vectors (K13); *formula* is arithmetic; *cited* is a vendor's report. The draft questions are LLM drafts. MiniLM was not available, so there are **no MiniLM margins or ranks** for the header arms here: run the verify notebook (`study/notebooks/I5_headers_verify.ipynb`) for yours. No API was called.

---

## 1. A chunk loses its context

**The setup.** Read the start of three v0 chunks the way the retriever sees them: alone.

```
chunk 34 (p.12)  It can be used for tracking carbon credits, verifying renewable energy ...
chunk 68 (p.23)  negative emissions. The captured CO2 can be stored or used ...
                 Chapter 16: Global Cooperation and Governance / International Agreements / Paris Agreement
                 The Paris Agreement is a landmark international accord ...
chunk 27 (p.10)  Chapter 6: Global and Local Climate Action / International Collaboration / ...
```

**The result** (measured, K4 and K9):

```
chunks with no heading line inside      0 of 97
chunks holding 2 or more headings      94 of 97
chunks that start on a heading         21 of 97
chunks that start mid-sentence         46 of 97   (the 200-character overlap cuts)
chunks that end on an orphaned heading 31 of 97   (16 of them at a page end, the count in 07 D.8)
```

**What this means.** A chunk is **contextually anonymous** when its meaning depends on text outside its span. Two kinds of context get lost:
- **Where it sits:** the chapter and section above it, its heading path. Chunk 68's Paris text belongs to Chapter 16, and only the headings say so.
- **What it refers to:** the subject behind "it", "this policy" or "the agreement". Chunk 34 opens with "It", meaning blockchain; the heading that names blockchain sits above the chunk, outside its span.

A retriever scores only the words inside the chunk, whether it embeds them or counts them. A chunk that says "It was adopted in 2015" shares almost nothing with the question "When was the Paris Agreement adopted?": the name lives in a heading or sentence before the span. An orphaned heading is the mirror case: a heading at the end of one chunk, its body in the next.

**The tempting wrong idea:** "a header adds facts to the chunk". It adds only context the document already had, a location or a referent. **A header restores context; it never adds evidence.**

Corpus D is **heading-dense**: every chunk already holds a heading, so expect a small effect. Papers (Corpus T), with few headings and phrases like "our method", are where headers can matter.

**For your project:** count these five numbers on your PDFs first; `study/tools/header_fit_check.py` prints them.

## 2. Where the header goes: embed_text, not text

**The setup.** A v0 chunk record holds `text`, `char_start`, `char_end` and its pages, with the span invariant `DOC[char_start:char_end] == text`. Add one field and leave the rest alone:

```python
embed_text = header + "\n\n" + text      # what the embedder sees at v1.2
# text, char_start, char_end: unchanged
```

**The result** (measured, K1 and K5):

```
span invariant DOC[char_start:char_end] == text      holds for all 97 chunks, in every arm
chunk 34, path arm, embed_text:
  Understanding Climate Change › Chapter 8: Future Directions and Innovations › Emerging Technologies › Blockchain for Climate Action

  It can be used for tracking carbon credits, ...
```

**What this means.** The header gets its own field because other readers depend on `text`:
- **The labels.** Gold evidence is stored as character spans, and CE@4 asks whether a retrieved chunk's span covers it. A header inside `text` breaks the invariant and shifts every offset, citations included.
- **The generator and BM25** read `text` too; whether they see a header is a separate decision.

So a header can enter three inputs, and each is its own decision:

| Input | Field | When it is tested |
|---|---|---|
| embedding | `embed_text` | **v1.2, this concept** |
| BM25 index | `bm25_text` | v2.0 (R1) |
| generation prompt | `display_text` | a later arm |

**v1.2 changes the embedding input only.** Questions stay as typed, so query vectors are reused unchanged across arms. The header template id becomes part of `preproc_version`, which changes `embed_hash`, so each arm gets its own index folder instead of sharing one.

**For your project:** one variable per experiment: the header template.

## 3. Get the headings from the PDF

**The setup.** PyMuPDF's `page.get_text("dict")` gives every text line with its font size and a bold flag (`flags & 16`). Group the lines by size and boldness:

```
size    bold   lines   level
24      yes        1   title       "Understanding Climate Change"
18      yes       22   chapter     21 chapters; Chapter 5's title wraps onto 2 lines and is merged
13.56   yes       68   section
12      yes      192   subsection
12      no       814   body text
```

**The result** (measured, K2):

```
PDF metadata title          ''   (empty: the title has to come from the 24 pt line)
headings by level           title 1 · chapter 21 · section 68 · subsection 192 · total 282
headings per page           min 1 · median 9 · max 11; all 33 pages have one
density                     one heading every 257 characters
subsections at body size    192 / 281 = 0.68 of the headings below the title
```

**What this means.** Font size alone is not enough. Two-thirds of the headings are 12 pt bold, the body size, so a detector that asks "bigger than body text?" misses them; the bold flag finds them. The metadata title is empty, so `doc.metadata["title"]` would give a blank header.

**For your project:** the full heading detector belongs to I2. I5 needs only this table and a check that every page has a heading.

## 4. The path, not the leaf

**The setup.** The **leaf** is the nearest heading above a chunk, such as "Paris Agreement". The **path** is the chain from the title down: title › chapter › section › subsection, joined by ` › `.

**The result** (measured, K3; tokens derived):

```
names reused under different chapters    11   (Paris Agreement, Smart Grids, Marine Ecosystems, ...)
p.10  Understanding Climate Change › Chapter 6: Global and Local Climate Action › International Collaboration › Paris Agreement
p.23  Understanding Climate Change › Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement
path length over 260 headings    75 / 120 / 168 characters (min / median / max) ≈ 12 / 19 / 27 tokens
```

**What this means.** A leaf-only header gives both Paris chunks the same label, so it cannot tell D-002's gold (p.10) from D-003's (p.23). Title and leaf are identical: **only the chapter and section levels separate them.** So the header is the full path.

**For your project:** list the leaf names your PDFs reuse. Many mean "full path".

## 5. Which heading a chunk gets

**The setup.** A 1,000-character chunk often spans several headings, so "the chunk's heading" needs a rule:
- **Start rule:** the path in effect at the chunk's first non-space character.
- **Majority rule:** the path that covers most of the chunk's non-space characters.
- **All-inside:** every heading inside the chunk, joined.

**The result** (measured, K4):

```
chunks holding ≥ 2 headings        94 of 97
start path ≠ majority path         84 of 97
all-inside header length           93 / 198 / 306 characters (min / median / max)

chunk 27 (p.10, D-002 gold)   starts on the Chapter 6 line
  start      Chapter 6: Global and Local Climate Action
  majority   Chapter 6 › International Collaboration › Paris Agreement
chunk 68 (p.23, D-003 gold)   starts with the last two lines of the DAC text, then Chapter 16
  start      Chapter 15: Climate Change and Technology › Carbon Capture and Utilization › Direct Air Capture (DAC)
  majority   Chapter 16: Global Cooperation and Governance › International Agreements › Paris Agreement
chunk 34 (p.12)               starts "It can be used for tracking carbon credits"   (it = blockchain)
  start      Chapter 8 › Emerging Technologies › Blockchain for Climate Action
  majority   Chapter 8 › Policy and Governance › Integrated Climate Policies
```

**What this means.** The start rule labels chunk 68's Paris text with Chapter 15, carbon capture: the wrong chapter for D-003. The majority rule gets it right. On chunk 27 the start rule stops at the chapter; the majority rule reaches "Paris Agreement". Chunk 34 goes the other way: its opening "It" means blockchain, which only the start rule names; the majority rule names the policy text that fills most of the chunk. **Neither rule wins on every chunk.** All-inside avoids the choice but makes long headers, up to 306 characters.

**The tempting wrong idea:** "a chunk's heading is simply the one it starts under". The two rules disagree on 84 of 97 chunks, so the rule is an experiment variable, not a detail.

**For your project:** the lesson's default arm is the majority rule; the start rule is the competing arm. Pre-register three arms for v1.2: none, start and majority. Run title-only on D only as an exploratory negative control (§6).

## 6. The information test: a constant title adds nothing

**The setup.** Count how many different headers each arm gives the 97 chunks.

**The result** (measured, K5 and K10):

```
arm               distinct headers   largest group sharing one header
none               1 / 97             97
title only         1 / 97             97
path (start)      97 / 97              1
path (majority)   96 / 97              2
BM25, title arm   understanding, climate, change in all 97 units → idf lifted to the floor 0.8565
```

**What this means.** A header can lift one chunk above another only if the two get **different** headers. The title arm puts the same 28 characters on every chunk: one distinct header out of 97, so there is nothing in it to rank by. It still does something: in a mean-pooled embedding the same tokens pull every vector a little toward the title's topic, so ranks can move, with no new information. That is why title-only is a control, not a candidate. In BM25 the three title words occur in every unit, so their idf would be negative; `rank_bm25` lifts each to a floor (0.8565), and every chunk gets nearly the same extra score.

A quick measure is **distinct headers ÷ chunks**. Near 1/97, the header is useless. Near 1, it varies.

**The tempting wrong idea:** "the title tells the model what the document is about, so it must help". With one document, every chunk comes from that document. A title carries information only when the corpus has several documents, as T does.

**For your project:** title-only is the negative control on D; test titles on T.

## 7. Dilution and the header magnet

**The setup.** MiniLM averages its token vectors (mean pooling). A header of h tokens on a chunk of c tokens takes a share `s = h / (h + c)` of that average.

**The result** (derived tokens, K6; toy, K13):

```
a ~19-token header (120 characters) on a chunk of
  ~161 tokens (1,000 characters)          s = 0.106
  ~151 tokens (935, the median chunk)     s = 0.112
  ~64 tokens (400 characters)             s = 0.229
path arm, header share by characters      0.029 / 0.119 / 0.201 (min / median / max)

toy: chunks A and B of 150 tokens on different topics, the same header on both (d = 64)
  h      s       cos(A + header, A bare)   cos(A, B), both with the header
  0      0.000   1.0000                    −0.1651
  19     0.112   0.9897                    −0.1857
  50     0.250   0.9423                    −0.1265
  100    0.400   0.8014                    +0.0964
```

**What this means.** A small share barely moves a chunk's vector (0.9897 at s = 0.112 in the toy). The same header doubles its share on a short chunk, so short chunks move more. A large shared header pulls unrelated chunks toward each other and toward its own topic: the **header magnet**. In the toy, two chunks on different topics turn from a negative cosine to a positive one at s = 0.400. That hurts when a gold chunk and its distractor share a header. Toy magnitudes, not MiniLM.

**For your project:** report the median and maximum header share; be wary above about 0.25.

## 8. Truncation: the tail is cut

**The setup.** MiniLM reads at most 256 tokens, and its special tokens `[CLS]` and `[SEP]` count inside the 256. The header comes first in `embed_text`, so when `h + c > 256` the **end of the chunk** is dropped, not the header.

**The result** (derived, K6; the 182-token maximum chunk is cited from C2):

```
longest v0 chunk                 182 tokens, specials included
+ a 27-token path header         182 + 27  = 209 ≤ 256   fits
+ a 100-token LLM context        182 + 100 = 282 > 256   over by 26: the last 26 tokens of chunk text are cut
path arm over 256                0 of 97   (largest estimate 188)
100-token context over 256       about 29 of 97 chunks
```

**What this means.** A truncated chunk loses its last sentences silently: no error, just a vector built from less text. If the answer sat at the end, the header made the chunk harder to find. Path headers fit; 100-token LLM contexts do not, for about a third of the chunks.

**For your project:** check `h + c ≤ 256` for every chunk before embedding. Cap LLM contexts, or use an embedder with a larger window (Cohere `embed-v4.0`).

## 9. Measuring it on your questions

**The setup.** Compare the arms on the dev questions with CE@4 at a fixed k (CE@4: the top 4 contain the evidence). At v1.2 the header never enters the generator's context, so the arms read the same text and need no budget correction. Report:
- CE@4 per arm, and per category with its n;
- the discordant pairs: items one arm gets right and the other gets wrong;
- the cosine margin between the gold chunk and its near-duplicate distractor (D-002: p.10 against p.6, 23 and 24; D-003: p.23 against p.6 and 10), which needs no labels;
- a leakage check (below).

**The result** (measured BM25 preview, K10 and K8; formula, 06 §9.4):

```
BM25, the 8 answerable draft seeds    Hit@4 8/8 · CE@4 8/8 · MRR@10 0.938 in every arm (none, title, start, majority)
leakage                                no seed has a question word that is in its gold header but not in its text
n = 50 paired questions                95% half-width ±0.124; about 0.18 needed for 80% power
MiniLM per arm                         not measured here: run the verify notebook
```

**What this means.** BM25 is at the ceiling on these span-written seeds, so they cannot show a header effect either way. With about 50 questions, a difference under about 18 points is likely noise. When results split, with headers helping one category and hurting another, check n and the discordant pairs first. Three flips in a category of six can be chance, and one item can sit in two groups: D-002 is a factual-single-span item tagged near-duplicate. Then read the items that got worse: a short gold chunk (a high share s), a header shared with the distractor (the magnet), or a header from the wrong rule (chunk 68).

**Header-query leakage.** If the questions were written from the headings, their words sit in the header but not in the chunk text, and the header "wins" by echoing the question. A large gain on such a set is suspect. For each question, list the content words that are in its gold chunk's header but not in its text, then re-test on questions written from the evidence spans.

**For your project:** fix the arms and the metric before you look.

## 10. LLM-written contexts and the cost ladder

**The setup.** Anthropic's contextual retrieval gives an LLM the whole document plus one chunk and asks for a 50–100-token context that situates the chunk. The context is prepended before embedding and before BM25 (cited). dsRAG instead writes a document-level header, a title and a summary, with one or two calls per document and none per chunk. Corpus D has 97 chunks and 12,840 document tokens in `o200k_harmony`, the Groq model's tokenizer; Claude counts differently, so its costs are a proxy.

**The result** (derived, K11; Groq's limits are UNVERIFIED):

```
rung  what                                   calls  input tokens per call  D cost
0     heading path (this lesson)              0     —                      $0
1     title / summary per document (dsRAG)    1–2   ≤ 4K–8K                not needed on D
2     chapter window, Groq gpt-oss-20b        97    median 855             $0.0124 · 106,743 tokens · ≥ 13.3 min at 8K TPM
3     whole document, Groq free tier          97    13,090                 blocked: one request > 8,000 TPM
      (and 97 calls = 1,269,730 input tokens against 200K tokens per day)
3     whole document, Haiku 5.5               97    13,090                 $0.1367 uncached · $0.0261 cached
```

**What this means.** Rung 3 is the only rung that can name what "it" refers to from anywhere in the document, and it is the expensive one. On Groq's free tier a single whole-document request (13,090 tokens) is larger than the 8,000 tokens-per-minute limit, so it fails on the very first call, and retrying cannot help. Two fixes: send a chapter window instead (rung 2), or run rung 3 on Haiku 5.5 with caching (or on a paid Groq tier, $0.0542).

**Late chunking** gets a similar effect with no LLM: a long-context embedder reads the whole document, then the token vectors are averaged per chunk span, so each chunk vector has "seen" its surroundings. It needs token-level outputs and a long window, and helps only the dense side. MiniLM's 256-token window is barely larger than one chunk, so here it adds nothing.

**For your project:** start at rung 0. Pay for rung 2 or 3 only if the path header helps.

## 11. Prompt caching, cache keys and wrong contexts

**The setup.** All 97 rung-3 prompts begin with the same 12,840-token document. Claude's prompt caching stores a prompt's prefix: the first call writes it (1.25× the input price, a 5-minute lifetime), and later calls that begin with the identical prefix read it (0.1×).

**The result** (derived, K11; cited from the research; measured, K12):

```
Haiku 5.5, whole document, 97 calls      uncached $0.1367 · cached $0.0261 (5.2× cheaper)
cookbook prompt of 3,412 tokens on Haiku 4.5 (minimum 4,096): nothing cached, and no error
one-line edit on page 12 (changes chunk 33 only), then rebuild:
  key = hash(chunk text)                               96 of 97 contexts served from cache: stale
  key = hash(prompt version + document + chunk)         0 of 97 served: all rebuilt
```

**What this means.** Caching needs an exact prefix. Put the document first and the chunk and instruction last, and process the chunks in document order so the entry stays warm. It misses **silently** when the prefix is below the model's minimum (512 tokens on Haiku 5.5, 4,096 on Haiku 4.5; check the docs), when anything before the document changes from call to call, or when calls are shuffled and the entry expires. You see it only in each response's cache-write and cache-read token counts.

A context depends on the whole document, not only on its chunk. After the page-12 edit, a key over the chunk text still matched for 96 chunks, so their old contexts came back although the document had changed. The key must hold the prompt version, the full document text (store its `doc_text_sha256` with each context) and the chunk text.

LLM contexts can also be wrong: a name or number not in the document, or the wrong section. Check each context's capitalised words and numbers against the document, and hand-read ten.

**For your project:** log cache-write and cache-read tokens on every call, and rebuild a document's contexts whenever its hash changes.

## 12. Reading the vendor numbers

**The setup.** Anthropic measured **1 − recall@20**: the share of relevant chunks missing from the top 20. We measure CE@4. A change can be stated as absolute, `b − a`, or relative, `(b − a) / a`.

**The result** (formula, K15; cited; measured, K14):

```
Anthropic, 1 − recall@20               absolute      relative
5.7% → 3.7%   contextual embeddings    −2.0 points   −35.1%
5.7% → 2.9%   + contextual BM25        −2.8 points   −49.1%
5.7% → 1.9%   + reranking              −3.8 points   −66.7%
Anthropic cookbook, Pass@10            87.15 → 92.34 (contextual) → 95.26 (+ reranking)
dsRAG KITE (0–10, LLM judge)           4.72 → 6.04 with contextual headers
upstream notebook, cell 13             0.10576342 → 0.92206234: a Cohere reranker score for one Nike chunk,
                                       query "Nike climate change impact"
```

**What this means.** "35%" is a relative drop in missed chunks at top 20: two points absolute, on the vendor's data. It is not a 35-point gain, and not CE@4. With 50 questions we need about 18 points, so even a vendor effect that transferred whole would stay invisible. The upstream jump from 0.106 to 0.922 is a cross-encoder relevance score for one chunk and one query, and the query names the very entity the header adds ("Nike"). It is a constructed best case, not a retrieval metric. The course's notes on Ch7 read the book's 0.1 → 0.9 as the same kind of number.

**For your project:** turn every vendor claim into an absolute change on a named metric and k.

## 13. When not to use it

- **A title-only header on one document.** It carries no information; use the path, or nothing.
- **Chunks that are already self-contained** (FAQ entries, chunks that open on their own heading). Expect little.
- **No heading tree to detect** (one font size, no bold). There is no deterministic header; parse first (I2) or consider rung 2.
- **The LLM arm before the free arm.** Run rung 0 first and pay only if it helps.
- **A corpus that fits in the prompt.** Anthropic itself suggests sending a knowledge base of under about 200K tokens whole; Corpus D (12,840 tokens) is a teaching corpus here.
- **A long context on a 256-token embedder.** It cuts the chunk's tail.

## Check yourself

→ [`study/questions/I5_questions.md`](../questions/I5_questions.md): 2 cold questions before reading, 15 after, 1 for a later review, and 1 interview question.
