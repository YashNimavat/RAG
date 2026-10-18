<!-- kit:reading concept=C1 depth=short version=1 -->
# C1: Document loading and parsing

**What this is:** the short reading for C1, the text version of the HTML lesson's Short depth ([`study/lessons/C1_parsing.html`](../lessons/C1_parsing.html)). It follows the lesson's 12 steps in the same order and is enough to answer every question in [`study/questions/C1_questions.md`](../questions/C1_questions.md).
**What this is not:** the full lesson with the repo and book walk-throughs (the HTML lesson's Full depth), the old lab lesson ([concepts/C1_document_parsing.md](../../concepts/C1_document_parsing.md)), chunking (C2), or OCR and image captioning (S2).

**The answer first.**
1. A PDF stores glyphs drawn at positions, not paragraphs. A parser rebuilds text from them, and every later stage sees only what it rebuilt.
2. v0 reads each page with PyMuPDF 1.26.7 and keeps one record per page: document, page number counted from 1, raw text, parser and version.
3. All pages are joined into one text with `"\n"`. Chunks, citations and gold labels all point into that text by character offset, so the text is frozen and named by a `snapshot_id`.
4. Any change to the text, even one space or one Unicode normalisation, makes a new snapshot.
5. v0 cleans nothing. It measures the artifacts page by page; a cleaning rule or a second parser comes in only as a new, logged snapshot that must beat v0 on the questions that touch the affected pages.

> **Read in the book:** Ch1 p.4–5/14 and p.7/14 before §1; Ch2 p.4/11 before §4; Ch3 p.1/14 and Ch16 p.1/11, p.4/11, p.10/11 before §7. About 10 minutes. The book never mentions hyphenation, ligatures, reading order, OCR, named PDF libraries or snapshots.

**Labels used below.** *Measured* numbers come from our scripts on the climate PDF (Corpus D, 33 pages): [C1_FACTS](../../sources/verification/C1/C1_FACTS.md) rows S1–S12 and K1–K12. *Toy* means a made-up input: the 5-page **zoo** PDF (failures drawn on purpose), the two-column **paper page** (drawn column by column like a LaTeX paper, with an unruled table and made-up numbers), or a few short strings. A toy shows that an effect exists, not how often. *Formula* lines are arithmetic you can redo. *External* numbers come from a named paper, read 2026-10-17. *Research probe* numbers come from 8 candidate arXiv papers probed on 2026-10-17 for Corpus T, which is not chosen yet. No API was called to write this file.

---

## 1. Three silent problems

**The answer first:** a PDF reader can lose page numbers, change offsets or return nothing, and none of these raises an error.

**The setup.** The repo's `read_pdf_to_string` (`helper_functions.py` L223–L245) opens the climate PDF with PyMuPDF and glues the pages together with `content += page.get_text()`.

**The result** (measured, S4, S6, S9, S11):

```
repo string      72,561 characters, no page numbers, no separators
page 2 starts    2,424 in the repo string     vs 2,425 in our joined text
page 33 starts   71,925 in the repo string    vs 71,957 in our joined text
"Paris Agreement" first occurs at offset 13,420 of our text → page 6, page offset 1,874
                 the repo string gives an offset and nothing else: which page? You cannot say.
pypdf vs PyMuPDF same word sequence on 33 of 33 pages, identical text on 0 of 33
zoo p.3 and p.4  both return ""   (p.3 has 0 images, p.4 has 1 image)
```

**What this means.** Three problems, all silent:
- **Lost pages.** Without page numbers no answer can cite a page.
- **Same words, different text.** Each PyMuPDF page is the pypdf page plus one `"\n"` (33 of 33 pages). A gold label written as offsets on one parser's text points at the wrong characters on the other's.
- **Text that is not there.** A blank page and a page that is one picture give the same empty string.

**For your project:** v0 keeps pages, freezes one text and counts what each page contains. The rest of this reading builds those three habits.

## 2. What a PDF page really is

**The answer first:** a page is a list of drawing commands ("put these glyphs at x, y"), stored in the order the producing program wrote them. Paragraphs and reading order are not stored.

**The setup.** `page.get_text()` turns the text-drawing commands back into a string. By default it follows the file's own order (the content stream), grouped into blocks and lines.

**The result** (toy, K7, K8):

```
zoo p.1      drawn line by line across two columns   → lines come out L1 R1 L2 R2 ...   4 right→left jumps
paper page   drawn column by column (like LaTeX)     → left column, then right column    1 jump (into the table)
```

**What this means.** The order you get is the order in the file, not the order a person reads. A LaTeX paper usually stores one column after the other, so the default text is fine. A program that draws line by line across the page gives interleaved columns.

A page either has a **text layer** or it does not. A **born-digital** PDF (made by a program) has one. A **scanned** page is a photo of paper: it has an image and no text, so the parser returns `""`. OCR (optical character recognition) can create a text layer, with its own errors; that belongs to S2. One rule tells the cases apart:

```
chars(page) = 0  and  images(page) > 0   ⇒  image-only (scanned, or one big picture)
chars(page) = 0  and  images(page) = 0   ⇒  blank
```

On the zoo, page 3 is blank and page 4 is image-only (K7).

**For your project:** count characters and images on every page before you trust a page's text.

## 3. One record per page, numbered from 1

**The answer first:** v0 stores each page as `Page(doc_id, page, text, parser)`, with `page` counted from 1 and `text` exactly as `get_text()` returned it.

**The setup.** Load Corpus D page by page:

```python
import pymupdf
doc = pymupdf.open(path)
pages = [Page("climate", i + 1, p.get_text(), f"pymupdf {pymupdf.VersionBind}")
         for i, p in enumerate(doc)]                 # PyMuPDF counts from 0; our page from 1
```

**The result** (measured, S2, S4, K2):

```
33 records · page 1 ... 33 · shortest 636 characters (p.33) · longest 2,494 (p.19) · total 72,561
.strip() on every page        removes 70 characters        → every later offset moves
LangChain PyPDFLoader         0-based "page" metadata, .strip() on every page
the 37-character gap          PyPDFLoader 72,523 vs raw pypdf 72,560 = the per-page .strip()
```

**What this means.** The four fields carry what every later stage needs: which document, which page (for citations), the exact text (for offsets) and which parser made it (for the snapshot). Two defaults break this quietly. A 0-based page number cites page 5 for text on page 6. `.strip()` looks harmless, but it deletes characters, so the text and its hash are no longer the parser's output. LangChain's loaders do both (S11, K2).

Characters are not tokens: a page of 2,424 characters is a different number of LLM tokens, counted by the model's own tokenizer ([P1](P1_llm_fundamentals.md)).

**For your project:** assert `pages[0].page == 1`, never strip, and write the version into `parser`.

## 4. One coordinate system: the page table

**The answer first:** join the pages with one `"\n"`, record where each page starts and ends, and every offset in the joined text maps back to exactly one page.

**The setup.**

```
doc_text      = "\n".join(page texts)
start(1)      = 0
end(i)        = start(i) + len(page i)              # end is exclusive
start(i + 1)  = end(i) + 1                          # + 1 for the joining "\n"
page_of(x)    = the last row with start ≤ x         # the join character belongs to the page before
```

**The result** (measured, S2, S6):

```
len(doc_text) = 72,561 + 32 joins = 72,593
row  page 1  [0, 2,424)       page 2  [2,425, 4,835)      page 3  [4,836, 7,019)
page_of(2,424) = (1, 2,424)   ← the "\n" after page 1
page_of(2,425) = (2, 0)
page_of(13,420) = (6, 1,874)  "Paris Agreement"
"\n\n" in doc_text: 32, every one at a page join
```

**What this means.** The joined text is the one coordinate system for the whole course. A **span** `[start, end)` is a pair of offsets into it: `start` is the first character, `end` the first character after. A gold label (M1) is such a span, and so is a chunk (C2). Both stay valid only while the text stays exactly the same. Because no page holds a `"\n\n"`, C2's splitter, which tries `"\n\n"` first, can only cut at page joins.

A toy you can do by hand (toy, S12, K10): pages `"Ice melts.\n"`, `"Seas rise.\n"`, `"Act now.\n"` give a 33-character text and rows (1, 0, 11), (2, 12, 23), (3, 24, 33). Offset 11 is the join, so it belongs to page 1; offset 12 is (2, 0).

**For your project:** store the rows with the snapshot and check `doc_text[start:end] == page text` for every page.

## 5. Freeze the text: the snapshot id

**The answer first:** a hash names exact bytes, so v0 hashes the joined text together with the parser, its version, its options, the cleaning version and the join. The first 12 hex characters are the `snapshot_id`.

**The setup.** A hash (sha256) turns any bytes into a fixed-length code; change one byte and the code changes completely (toy, K5):

```
"Seas rise.\n"      63c2941c7f6b
"Seas rise. \n"     b1e07b17c9c7     ← one extra space
```

The recipe (06 §5.3):

```python
parts = ["snapshot-v1", f"parser={backend}@{version}", "options=" + json.dumps(options, sort_keys=True),
         f"cleaning={cleaning_version}", "page_join=\\n"]          # a literal backslash + n
parts += [f"{doc_id}:{doc_text_sha256[doc_id]}" for doc_id in sorted(doc_text_sha256)]
snapshot_id = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
```

**The result** (measured, S2, S3):

| Change one input | Text changed? | `snapshot_id` |
|---|---|---|
| none: PyMuPDF 1.26.7, options `{}`, cleaning `none` | — | `ea07572562ac` |
| version 1.28.2 | no (byte-identical) | `4b7e61b9e418` |
| cleaning `tabs_v1` (D has 0 tabs) | no | `6164dfc95324` |
| options `{"sort": true}` | not recomputed | `f1e46e7c3c68` |
| one extra space at the end of page 1 | yes | `a79df757e413` |
| `page_join` written as a real newline (a bug) | no | `5ad6acfd28ec` |

**What this means.** Five inputs feed the id: parser and version, options, cleaning version, the page join, and each document's text hash. **The id changes even when the text does not**, because a new version or rule is a new claim that must be checked again. Keep two things apart: the **PDF lock** hashes the PDF's bytes; the **snapshot** hashes the extracted text that offsets point into.

Add one page at the end (toy, K10): pages of 100, 50 and 80 characters have rows (1, 0, 100), (2, 101, 151), (3, 152, 232). A fourth page of 40 adds the row (4, 233, 273). Rows 1–3 do not move, but the text hash changes, so the id changes. Old labels still decode to the same characters, yet the dataset must be **rebound** to the new snapshot and re-validated (06 §5.3 rule 3).

**For your project:** every chunk, index and label carries the `snapshot_id`; a mismatch stops the run.

## 6. Characters are not bytes

**The answer first:** Python's `len` counts code points; a file holds bytes. They differ for non-ASCII characters, and Windows adds bytes of its own.

**The setup.** UTF-8 stores plain ASCII letters in 1 byte and other characters in 2–4. Corpus D has exactly one non-ASCII character, an em dash `—` on page 19, which takes 3 bytes.

**The result** (measured, S7, K3):

```
doc_text                       72,593 characters    72,595 UTF-8 bytes   (one "—": +2)
open(path, "w")  on Windows    73,727 bytes          each of the 1,132 "\n" became "\r\n"; hash ≠ doc_text_sha256
open(path, "w", newline="\n")  72,595 bytes          hash = doc_text_sha256
```

**What this means.** Reading the file back in text mode turns `"\r\n"` into `"\n"` again, so the bug hides; only the bytes on disk show it. Offsets are always character offsets into the string, never byte positions in a file.

**For your project:** write every snapshot with `encoding="utf-8", newline="\n"`, then hash the file's bytes in a test.

## 7. The artifact catalogue, and one check for each

**The answer first:** extraction leaves predictable artifacts. You do not fix them in v0; you detect each one with a cheap check and count it per page.

**The setup.** Three inputs: Corpus D (a real, clean, one-column report), the zoo (broken on purpose) and the paper page (a two-column toy like a LaTeX paper).

**The result** (measured S5, K9; toy K7, K8):

```
Corpus D     0 images · 0 right→left jumps · 0 ligatures · no repeated lines · 0 tables
             7 line-end hyphens, all real compounds (well-being, decision-making, ...)
             24 of 32 page breaks end without final punctuation; 8 continue mid-sentence
zoo          p.1: columns interleaved, 4 jumps; header and footer on 3 pages, the footer comes out second
             p.2: ruled table found (3 × 2, correct) · p.3 blank · p.4 image-only
paper page   default order correct, 1 jump · sort=True puts words of both columns on 3 lines
             unruled table: lines strategy finds 0; text strategy finds a 23 × 9 "table" that swallows the page
             the table comes out one cell per line: Method, NQ, TQA, SQuAD, BM25, 59.1, ...
```

| Artifact | What you see | One check |
|---|---|---|
| Line-end hyphen | `cost-\ncompetitive` | regex `[A-Za-z]-\n[a-z]`; then: does the joined word occur elsewhere? |
| Ligature | `ﬁ` as one character; "file" not found | count U+FB00–FB06 |
| Header / footer | the same line on many pages | same line (digits masked) on ≥ max(3, ⌈n/2⌉) pages |
| Columns read across | sentences that jump between columns | right→left jumps between body lines |
| Flattened table | one cell per line, rows lost | `find_tables()` hits; or many short number lines and no table found |
| Figure | nothing (only a text caption) | an image on the page with no text inside its area (Ch16 p.1/11) |
| Blank vs image-only | `""` for both | chars = 0, then count images |
| Equation | symbols out of order; `x²` → `x2` under NFKC | share of lines that are mostly symbols |
| Page-break cut | a sentence split over two pages | page ends without final punctuation, next starts lower-case |
| Encoding failure | `�` or `(cid:N)` strings | count U+FFFD and `(cid:` (0 on D, K9) |

**What this means.** Reading order follows the PDF's content stream, so it depends on the program that made the file. LaTeX papers are mostly fine; line-by-line producers fail (the zoo). `sort=True` is not a fix: it sorts by height and merges lines of both columns. The research probe of 8 candidate papers for Corpus T (research probe, 2026-10-17) found a different mix from D: 15–323 line-end hyphens per paper, 0–157 ligatures, 1–4 right→left jumps per paper, and one paper (RAPTOR) with a running header on every page. The book shows the header/footer symptom from the retrieval side: a retrieved chunk that is a page footer full of links scores well and adds only noise (Ch3 p.1/14).

**For your project:** Corpus D's numbers say nothing about Corpus T. Count the artifacts on T once it is chosen.

## 8. Normalisation moves every later offset

**The answer first:** Unicode normalisation (NFKC) rewrites characters into plain forms, and many rewrites change the length. Every offset after a change moves.

**The setup.** NFKC on single strings (toy, K3):

```
character         NFKC     length change
ﬁ  (U+FB01)       fi       +1
ﬂ  (U+FB02)       fl       +1
…  (U+2026)       ...      +2
½  (U+00BD)       1⁄2      +2
x² (x + U+00B2)   x2       +0, but the exponent is lost
e + U+0301        é        −1
no-break space    space    +0
```

**The result** (toy, K4): a 520-character page with ligatures at raw offsets 100 and 300. After NFKC it has 522 characters, and the character at raw offset 500 is now at 502:

```
cleaned 101 ← raw 100      (the ligature's second letter)
cleaned 102 ← raw 101
cleaned 502 ← raw 500      (+1 for each ligature before it)
```

**What this means.** A label written as `[500, 510)` on the raw text points two characters too early after NFKC. On Corpus D NFKC changes 0 characters (K3), but the research probe found +108 characters on DPR and +160 on BERT (research probe, 2026-10-17). NFKC also changes meaning (`x²` → `x2`).

**For your project:** never normalise the snapshot in place. If ligatures must go, rule R3 (§9) replaces only U+FB00–FB06, as logged edits with a map back to the raw text.

## 9. Cleaning as logged edits, and why v0 applies none

**The answer first:** if you clean, record every change as an edit with raw offsets, so every cleaned character can be traced to its raw position and the raw text can be rebuilt exactly. v0 applies no edits at all.

**The setup.** An edit is `{page, rule, start, end, before, after}` on raw page offsets. Applying the edits gives the cleaned text plus a map `src[i]` = the raw offset of cleaned character `i`. `undo(apply(edits)) == raw` must hold. Three rules, run as reports:

```
R1  drop a line that repeats (digits masked) on ≥ max(3, ⌈n/2⌉) pages     headers and footers
R2  delete "-\n" only if the joined word occurs elsewhere in the document   line-end hyphens
R3  replace a ligature (U+FB00–FB06) by its letters                         ligatures only, not full NFKC
```

**The result** (toy S10, K11; measured S5, S8, S10):

```
zoo          R1 6 · R2 1 · R3 3 edits · 92 raw characters removed, 6 inserted · undo(apply) == raw on every page
paper page   R2 joins accu-racy ("accuracy" occurs elsewhere), leaves mar-gin ("margin" does not)
             R2 + R3: 575 → 576 characters · undo(apply) == raw
index.pdf    R1 flags 5 real section titles (false positives)
Corpus D     all three rules: 0 edits · a naive "-\n" join would damage 7 of 7 compounds
```

R2 deletes only the two characters `-\n`, so the letters around them keep their raw offsets: after the edit, every cleaned offset from the hyphen on maps to raw offset + 2.

**What this means.** On Corpus D cleaning would change nothing, and the obvious de-hyphenation rule would only do harm. Rules also make mistakes (R1 on `index.pdf`), so a rule needs a log and a look. A cleaning version is part of the snapshot: the paper page gets three different ids for cleaning `none`, `r3_ligatures_v1` and `r2r3_v1` (toy, K12). The book cleans *after* splitting into chunks (Ch1 p.5/14, p.7/14), and so does the repo (`helper_functions.py` L69–L70); then a chunk's text is no longer a slice of any stored text.

**For your project:** v0 keeps `cleaning: none`. If Corpus T's artifact log justifies R2 or R3, it runs before chunking, gets a version string and makes a new snapshot.

## 10. Parsers compared: what the extra cost buys

**The answer first:** cheap text extractors are already good at text on born-digital pages. Layout models and vision-language models (VLMs) buy structure (reading order, tables, formulas) at a much higher cost.

**The setup.** Three families:

| Family | Examples | Gives | Cost |
|---|---|---|---|
| Text extractors | PyMuPDF, pypdf, pdfplumber | text per page, positions | fast, small install |
| Layout models | Docling, unstructured `hi_res`, marker | reading order, tables, sections | seconds per CPU page, large install |
| VLMs | a vision model reads the page image | Markdown from the picture | one model call per page |

**The result** (external, read 2026-10-17):

```
[C1-3] scientific pages, text F1      PyMuPDF 0.840 · pypdfium2 0.853 · pypdf 0.764        (a preprint)
[C1-3] table detection F1             Table Transformer 0.913 · PyMuPDF 0.179 · pdfplumber 0.062
[C1-1] seconds per page, x86 CPU      Docling 3.1 · Marker over 16                           (speed only)
[C1-2] OmniDocBench                   ignores headers, footers and page numbers when scoring; no PyMuPDF
```

**What this means.** For text, the pinned PyMuPDF is in the top group, so the pin costs little. For tables on scientific pages, no rule-based tool is good. Each benchmark has limits: one is a preprint, one measures speed only, and one skips exactly the lines that pollute RAG chunks. **A benchmark score belongs to its own pages, not to your corpus.**

**For your project:** PyMuPDF 1.26.7 stays pinned (licence AGPL-3.0, fine for personal study). Docling (MIT) is a possible comparison arm, as its own snapshot (`parser=docling@2.133.0`), never a silent swap.

## 11. Measuring parse quality, in three separate steps

**The answer first:** first check the extraction on its own; then ask whether it matters for retrieval; answer quality is a third, separate measurement.

**The setup and the steps.**
1. **Extraction on its own** (a component check). Compute the per-page signals of §7, read a stratified hand sample side by side with the rendered page (some pages from each flag), and diff against a second parser. The AI Eval book makes the same point: check the PDF extraction step by itself, and look at the text the model actually received, before you blame the model (AE Ch8, 'PDF Documents').
2. **Does it matter for retrieval?** Only through questions. Split the eval questions into those whose gold spans lie on flagged pages and the rest. Build the index from both snapshots (v0 and the arm) and compare **Hit@k** (1 if at least one right chunk is in the top k, else 0) and **CE@k** (1 only if the top k holds all the evidence the question needs; P6 teaches it) on each group.
3. **Answer quality** (faithfulness, correctness) is measured later (C5, M3), never mixed into steps 1 and 2.

**The result.** Nothing is measured yet: there is no eval set before M1. The method is what matters:

```
flagged pages with no questions on them   → risk, not harm: leave v0 alone
questions on flagged pages                 → compare Hit@k / CE@k on those questions, v0 vs the arm
```

**What this means.** A parser change can only help or hurt through the questions whose evidence sits on the pages it changes. A page that looks ugly but feeds no question costs nothing. Gold spans belong to one snapshot, so the second arm's spans must be re-validated before you compare.

**For your project:** the apply-it tool (`study/tools/parse_quality_check.py`) prints these signals per page and which questions touch flagged pages.

## 12. For your project

**The answer first:** freeze Corpus T and its parsing decisions before M1 writes any labels, because labels are offsets into one snapshot.

**The setup.** Corpus T is still open (DEC-3). The research proposes two example sets from the 8 candidates: (a) about 93 pages, (b) about 100 pages (research probe, 2026-10-17). You choose.

**The result** (v0 decisions):

| Question | v0 decision | Why |
|---|---|---|
| Reader | PyMuPDF `get_text()`, pinned 1.26.7 | reproducible text and id (§5) |
| Page number | 1-based `page` in every record | citations count from 1 (§3) |
| Coordinates | one joined text, `"\n"` joins, page table | one system for chunks and labels (§4) |
| Cleaning | none; R1–R3 run as reports | offsets stay raw; D gains nothing (§9) |
| Normalisation | never in place | it moves offsets (§8) |
| Files | UTF-8, `newline="\n"`, validated before use | Windows bytes (§6) |
| A better parser | a comparison arm with its own `snapshot_id` | judged on questions (§10, §11) |

**What this means.** If T's artifact log shows that R2 or R3 is needed, adopt it **before** M1, so the labels are written on the final text. Adopting it later means a new snapshot and rebinding every label.

**For your project:** C1 hands C2 and C3 five things: `pages` (a list of `Page`), `doc_text`, the page-table rows `{page, doc_char_start, doc_char_end, text_sha256}`, the manifest, and the `snapshot_id` (`ea07572562ac` for Corpus D).

## 13. When not to clean or switch parsers

- **Do not clean when the rule cannot be shown to help on your questions.** On Corpus D every rule changes nothing or does harm.
- **Do not clean once labels exist**, unless you rebind them to the new snapshot.
- **Do not adopt a rule whose false positives you have not looked at** (R1 on `index.pdf`).
- **Do not switch parsers because of a benchmark.** Run the new parser as an arm and compare on your own questions.
- **Do not reach for OCR or a VLM** when the pages have a text layer and no question needs a figure; the book says captioning is overkill when tables already come out as usable text (Ch16 p.10/11).
- **Do not generalise from a toy.** The zoo and the paper page show that an effect exists, not how often.

What C1 does not cover: chunking (C2), embedding and the index manifest (C3), span labels (M1), the metrics (P6, M2), OCR and figures (S2).

## Check yourself

→ [`study/questions/C1_questions.md`](../questions/C1_questions.md): 2 cold questions before reading, 12 after, and 1 interview question. Answer the next day, closed book.
