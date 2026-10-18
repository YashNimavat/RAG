<!-- kit:questions concept=C1 version=1 -->
# C1 questions: page records, the page table, the snapshot id, artifacts and cleaning

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/C1/c1_measure.py` and `c1_kit_measure.py` on the climate PDF (Corpus D), the synthetic zoo PDF and the synthetic two-column paper page ([C1_FACTS](../../sources/verification/C1/C1_FACTS.md) S1–S12 and K1–K12). Parser benchmark numbers are **external** (research file, Concept C1 §5, read 2026-10-17). "Toy" inputs are made up: they show that an effect exists, not how often. Small page lengths in the Application items are toy data, and their answers are arithmetic shown in the answer. No API was called to write this file.

<!-- q id=C1-PRE-01 type=R set=pre -->
### C1-PRE-01 · Recall (before reading)
**Question:** What comes out of a parser for each page, and what must travel with it?

**Reply template:** `For each page the parser gives ____. With it I must keep ____, ____ and ____.`

<details><summary>Hint 1</summary>

Think about what a later answer needs in order to say "see page 6 of the climate report".

</details>

<details><summary>Hint 2</summary>

The text depends on which program read the PDF. What would you need to record so that someone can rebuild exactly the same text?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** One plain string per page: the text the parser rebuilt from the page's drawing commands, in the order the file stores them. It has line breaks, not paragraphs, and it can be empty. With it travel the document id, the page number counted from 1, and the parser with its version, because another parser or version can give different text. v0 stores exactly that:

```
Page(doc_id="climate", page=1..33, text=<raw get_text()>, parser="pymupdf 1.26.7")
```

**Key points** (a 3 needs every point):
- [ ] A plain text string per page, rebuilt from drawn glyphs (no paragraphs or reading order stored).
- [ ] The document id and the page number, counted from 1.
- [ ] The parser and its version.

**For a 4, also:**
- [ ] Names a case where the string misleads: an empty string can be a blank page or a scanned (image-only) page, and only the image count tells them apart (zoo p.3: 0 images, p.4: 1 image).

**Common wrong answers:**
- [ ] "The parser gives paragraphs and headings": a plain extractor gives lines in the file's order; structure has to be rebuilt.
- [ ] "The library's page index is the page number": PyMuPDF counts from 0, so page 1 would be cited as page 0.

**If you missed it, reread:** [short §2](../reading/C1_parsing.md#2-what-a-pdf-page-really-is) · [short §3](../reading/C1_parsing.md#3-one-record-per-page-numbered-from-1) · [lesson #page](../lessons/C1_parsing.html#page) · [lesson #records](../lessons/C1_parsing.html#records) · book Ch1 p.4/14 and Ch16 p.4/11

</details>
<!-- /q -->

<!-- q id=C1-PRE-02 type=R set=pre -->
### C1-PRE-02 · Recall (before reading)
**Question:** Two libraries give the same words. Are the character offsets the same?

**Reply template:** `____, because offsets need ____. Example: ____.`

<details><summary>Hint 1</summary>

An offset counts every character, including spaces and newlines, not just words.

</details>

<details><summary>Hint 2</summary>

If one library ends each page with one extra newline, what happens to where page 2 starts in the joined text?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** No, not in general. An offset counts characters, so it needs the exact same text, not just the same words. On Corpus D, pypdf and PyMuPDF give the same word sequence on every page, yet not one page is identical: each PyMuPDF page is the pypdf page plus a final `"\n"`. So a span written on one text points at the wrong characters on the other, and the gap grows by one character per page.

```
pypdf vs PyMuPDF on Corpus D:   same words 33 of 33 pages   ·   identical text 0 of 33 pages
```

**Key points** (a 3 needs every point):
- [ ] No: offsets need character-identical text; the same words are not enough.
- [ ] Evidence or mechanism: whitespace and newlines differ (D: same words 33/33, identical 0/33; PyMuPDF adds a final `"\n"`).

**For a 4, also:**
- [ ] Draws the consequence: labels and chunks belong to one parser's text, which is why the parser and version are inside the `snapshot_id`; compare text hashes, not words.

**Common wrong answers:**
- [ ] "Yes, the same words means the same positions": one extra newline per page already moves every later offset.
- [ ] "Only the page numbers can differ": the characters inside pages differ too.

**If you missed it, reread:** [short §1](../reading/C1_parsing.md#1-three-silent-problems) · [short §4](../reading/C1_parsing.md#4-one-coordinate-system-the-page-table) · [lesson #lost](../lessons/C1_parsing.html#lost) · [lesson #offsets](../lessons/C1_parsing.html#offsets) · book Ch1 p.4/14

</details>
<!-- /q -->

<!-- q id=C1-R-01 type=R set=main -->
### C1-R-01 · Recall
**Question:** What are the four fields of a v0 page record?

**Reply template:** `Page(____, ____, ____, ____)`

<details><summary>Hint 1</summary>

Which document, which page, what text, and who made the text?

</details>

<details><summary>Hint 2</summary>

For each field, say how v0 fills it: counted from what, and changed or raw?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** `Page(doc_id, page, text, parser)`.

```
doc_id   "climate"                       which document
page     1 ... 33, counted from 1        what a citation shows
text     raw page.get_text(), no strip   what every offset points into
parser   "pymupdf 1.26.7"                which program and version made the text
```

**Key points** (a 3 needs every point):
- [ ] `doc_id` and `page`, with `page` counted from 1.
- [ ] `text` exactly as the parser returned it (no `.strip()`, no cleaning).
- [ ] `parser` with its version.

**For a 4, also:**
- [ ] Says why each field matters: page for citations, raw text for offsets and the text hash, parser@version for the `snapshot_id`; and that Corpus D gives 33 records, 636 to 2,494 characters each.

**Common wrong answers:**
- [ ] "`page = i` from `enumerate`": that is 0-based; v0 stores `i + 1`.
- [ ] "Store the stripped text, it is cleaner": `.strip()` removes 70 characters on Corpus D and moves offsets.

**If you missed it, reread:** [short §3](../reading/C1_parsing.md#3-one-record-per-page-numbered-from-1) · [lesson #records](../lessons/C1_parsing.html#records) · book Ch14 p.5/13 (chunks tagged with their page)

</details>
<!-- /q -->

<!-- q id=C1-R-02 type=R set=main -->
### C1-R-02 · Recall
**Question:** What are the five inputs of the `snapshot_id`, and which change alters it even when the text is identical?

**Reply template:** `Inputs: ____, ____, ____, ____, ____. With identical text, ____ still changes it, because ____.`

<details><summary>Hint 1</summary>

Two inputs are about the parser, one about cleaning, one about how pages are joined, and one about the text itself.

</details>

<details><summary>Hint 2</summary>

PyMuPDF 1.28.2 gave byte-identical text on Corpus D. Is the version in the recipe or not?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The parser and its version, the options, the cleaning version, the page join, and each document's text hash (with its `doc_id`). They are joined into one string and hashed; the first 12 hex characters are the id. Changing the version alone changes the id, although the text is byte-identical:

```
PyMuPDF 1.26.7, options {}, cleaning none     ea07572562ac
same text, version 1.28.2                     4b7e61b9e418
same text, cleaning tabs_v1 (D has 0 tabs)    6164dfc95324
```

**Key points** (a 3 needs every point):
- [ ] Parser and version.
- [ ] Options and cleaning version.
- [ ] Page join and each document's text hash.
- [ ] A change with identical text that still changes the id (version 1.28.2, or a cleaning version that edits nothing).

**For a 4, also:**
- [ ] Explains why and draws one boundary: a new version or rule is a claim that must be re-checked, and the id makes that explicit; the PDF lock hashes the PDF's bytes, while the snapshot hashes the extracted text.

**Common wrong answers:**
- [ ] "Only the text hash: same text, same id": the version and the cleaning version are in the recipe too.
- [ ] "It is the hash of the PDF file": that is the PDF lock, not the snapshot.

**If you missed it, reread:** [short §5](../reading/C1_parsing.md#5-freeze-the-text-the-snapshot-id) · [lesson #snapshot](../lessons/C1_parsing.html#snapshot) · book Ch1 p.4/14 (the book has no snapshot; it only says weak extraction weakens what follows)

</details>
<!-- /q -->

<!-- q id=C1-R-03 type=R set=main -->
### C1-R-03 · Recall
**Question:** Why does v0 do no cleaning, and what does Corpus D show?

**Reply template:** `Because chunks and labels ____, and any cleaning ____. On Corpus D, ____.`

<details><summary>Hint 1</summary>

What do a chunk and a gold label store about their text?

</details>

<details><summary>Hint 2</summary>

Run R1, R2 and R3 on Corpus D in your head: what do they change? And what would the obvious "join every `-\n`" rule do to words like well-being?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Chunks and gold labels point into the raw snapshot by character offset. Any cleaning edits the text, so it moves offsets and creates a new snapshot (a new cleaning version, a new `snapshot_id`), which must earn its place by measurement. On Corpus D it would earn nothing:

```
R1 headers/footers · R2 safe de-hyphenation · R3 ligatures     0 edits on Corpus D
naive "-\n" join                                               damages 7 of 7 (all real compounds: well-being, ...)
```

**Key points** (a 3 needs every point):
- [ ] Chunks and labels are offsets into the raw text; editing moves them.
- [ ] Cleaning = a new cleaning version = a new snapshot, so labels must be rebound.
- [ ] Corpus D evidence: the three rules make 0 edits; naive de-hyphenation would damage 7 of 7.

**For a 4, also:**
- [ ] States the limit: the evidence is Corpus D only; the Corpus T probe found 15–323 line-end hyphens per paper (research probe), so T's artifact log may justify R2 or R3, as logged edits, before M1. Rules also have false positives (R1 flags 5 real titles in the book's `index.pdf`).

**Common wrong answers:**
- [ ] "Cleaning always helps, the book says dirty text gives noisy embeddings": that is a claim to test; and the book cleans after splitting, so chunk text is no longer a slice of stored text.
- [ ] "v0 skips cleaning because PyMuPDF already cleans the text": PyMuPDF keeps hyphens and ligatures by default.

**If you missed it, reread:** [short §9](../reading/C1_parsing.md#9-cleaning-as-logged-edits-and-why-v0-applies-none) · [short §12](../reading/C1_parsing.md#12-for-your-project) · [lesson #cleaning](../lessons/C1_parsing.html#cleaning) · book Ch1 p.5/14 and p.7/14

</details>
<!-- /q -->

<!-- q id=C1-R-04 type=R set=main -->
### C1-R-04 · Recall
**Question:** Name four extraction artifacts, each with a check a script can run to detect it.

**Reply template:** `____ → check ____; ____ → check ____; ____ → check ____; ____ → check ____.`

<details><summary>Hint 1</summary>

Think of words broken at line ends, special letter pairs, lines that repeat on every page, columns, tables, pictures and empty pages.

</details>

<details><summary>Hint 2</summary>

For each one, what can you count: a regex, a range of code points, a line seen on many pages, the order of line positions, an image count?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Any four, each with its check:

```
line-end hyphen      regex [A-Za-z]-\n[a-z]; then: does the joined word occur elsewhere?
ligature             count characters U+FB00–FB06 ("ﬁ" makes a search for "file" fail)
header / footer      the same line (digits masked) on ≥ max(3, ⌈n/2⌉) pages
columns read across  right→left jumps between body lines (zoo p.1: 4)
flattened table      find_tables() hits, or many short number lines and no table found
blank vs image-only  chars = 0, then count images (zoo p.3: 0 images, p.4: 1)
page-break cut       page ends without final punctuation and the next starts lower-case (D: 8)
```

**Key points** (a 3 needs every point):
- [ ] Four different artifacts from the catalogue.
- [ ] A concrete, countable check for each (not just "look at it").
- [ ] If an empty page is named: telling blank from image-only needs the image count, because the text is `""` for both.

**For a 4, also:**
- [ ] Gives a limit of one check: R1's repeated-line rule flags real section titles (`index.pdf`), or table detection by ruling lines finds 0 on an unruled table while the text strategy over-detects (23 × 9 on the paper page); and counts are per corpus (Corpus D has almost none).

**Common wrong answers:**
- [ ] "Two-column pages always come out interleaved": order follows the file; the column-by-column paper page comes out right (1 jump), the line-by-line zoo does not.
- [ ] "Search the text for strange characters": that misses hyphens, columns, tables and empty pages, which are all plain ASCII or nothing.

**If you missed it, reread:** [short §7](../reading/C1_parsing.md#7-the-artifact-catalogue-and-one-check-for-each) · [short §2](../reading/C1_parsing.md#2-what-a-pdf-page-really-is) · [lesson #artifacts](../lessons/C1_parsing.html#artifacts) · book Ch3 p.1/14 and Ch16 p.1/11

</details>
<!-- /q -->

<!-- q id=C1-R-05 type=R set=main -->
### C1-R-05 · Recall
**Question:** Why is NFKC normalisation of the whole text unsafe for a frozen snapshot?

**Reply template:** `Because NFKC ____, so every later offset ____. Instead I would ____.`

<details><summary>Hint 1</summary>

How many characters is `ﬁ` before NFKC, and how many after?

</details>

<details><summary>Hint 2</summary>

A gold label says `[500, 510)`. What happens to it if two characters before 500 each grow by one?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** NFKC rewrites characters into plain forms, and many rewrites change the length. Every offset after a change moves by the sum of the changes before it, so frozen labels and chunks point at the wrong characters, and the text hash and `snapshot_id` change. It can also change meaning.

```
ﬁ → fi  +1     … → ...  +2     ½ → 1⁄2  +2     x² → x2  +0, exponent lost
toy page, ligatures at raw 100 and 300:   raw offset 500 → 502 after NFKC
Corpus D: 0 characters change · research probe: DPR +108, BERT +160
```

**Key points** (a 3 needs every point):
- [ ] NFKC changes the length of some characters.
- [ ] Every later offset shifts by the sum of the changes before it (500 → 502 in the toy).
- [ ] Frozen labels and chunks then point at the wrong text, and the snapshot changes.

**For a 4, also:**
- [ ] Gives the safe alternative: rule R3 replaces only ligatures (U+FB00–FB06), as logged edits with a `src[i]` map to raw offsets, under a new cleaning version; and names the meaning loss (`x²` → `x2`).

**Common wrong answers:**
- [ ] "NFKC only makes characters look alike, so the length stays the same": `ﬁ` becomes two characters, `…` three.
- [ ] "It is harmless on Corpus D, so it is harmless": D has 0 changes; the candidate papers have up to 160.

**If you missed it, reread:** [short §8](../reading/C1_parsing.md#8-normalisation-moves-every-later-offset) · [short §6](../reading/C1_parsing.md#6-characters-are-not-bytes) · [lesson #unicode](../lessons/C1_parsing.html#unicode) · book Ch1 p.5/14 (the book's cleaning step never mentions Unicode)

</details>
<!-- /q -->

<!-- q id=C1-A-01 type=A set=main -->
### C1-A-01 · Application (page table by hand)
**Question:** Three pages of 100, 50 and 80 characters are joined with one `"\n"` between pages: where does page 3 start in the joined text?

**Reply template:** `Page 3 starts at ____ + ____ + ____ + ____ = ____.`

<details><summary>Hint 1</summary>

Each start is the previous page's end plus one, for the joining newline.

</details>

<details><summary>Hint 2</summary>

Page 1 is [0, 100). Where does page 2 start, and where does it end?

</details>

<details><summary>Hint 3</summary>

Page 2 starts at 100 + 1 = 101 and ends at 101 + 50 = 151.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** At 152.

```
page 1   [0, 100)
page 2   [101, 151)        101 = 100 + 1
page 3   [152, 232)        152 = 100 + 1 + 50 + 1
total length 100 + 50 + 80 + 2 joins = 232 = end of page 3
```

**Key points** (a 3 needs every point):
- [ ] Page 2 starts at 101 (one join after page 1).
- [ ] Page 3 starts at 152.

**For a 4, also:**
- [ ] Self-checks: the total length 100 + 50 + 80 + 2 = 232 equals page 3's end (152 + 80); and says the join at offset 100 belongs to page 1.

**Common wrong answers:**
- [ ] "150, the first two pages added up": that forgets the two joining newlines.
- [ ] "151": that is page 2's end (exclusive), not page 3's start.

**If you missed it, reread:** [short §4](../reading/C1_parsing.md#4-one-coordinate-system-the-page-table) · [lesson #offsets](../lessons/C1_parsing.html#offsets) · book Ch2 p.4/11 (a PDF read as one continuous stream)

</details>
<!-- /q -->

<!-- q id=C1-A-02 type=A set=main -->
### C1-A-02 · Application (one page added at the end)
**Question:** The same three pages (100, 50, 80 characters) get a fourth page of 40 characters at the end: which page-table rows change, does the `snapshot_id` change, and what happens to labels already written?

**Reply template:** `Rows ____ stay; row ____ is added. The id ____ because ____. The labels ____.`

<details><summary>Hint 1</summary>

Does anything before the end of page 3 move?

</details>

<details><summary>Hint 2</summary>

What is in the id's recipe that must differ now, even though pages 1–3 are untouched?

</details>

<details><summary>Hint 3</summary>

Page 3 ends at 232, so page 4 starts at 233.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Rows 1–3 stay exactly as they were; one row is added. The joined text is longer, so its hash changes, and with it the `snapshot_id`. Old labels on pages 1–3 still decode to the same characters, but the dataset must be rebound to the new snapshot and re-validated (06 §5.3 rule 3). Page 4 may also hold evidence that the old labels never saw.

```
before   (1, 0, 100)  (2, 101, 151)  (3, 152, 232)                    length 232
after    (1, 0, 100)  (2, 101, 151)  (3, 152, 232)  (4, 233, 273)     length 273
```

**Key points** (a 3 needs every point):
- [ ] Rows 1–3 do not change.
- [ ] A row (4, 233, 273) is added.
- [ ] The id changes, because the text hash changes.
- [ ] Labels are rebound to the new snapshot and re-validated.

**For a 4, also:**
- [ ] Contrasts with a change at the front: if page 1 changes length, every later row and offset moves (toy: page 1 doubled to 22 characters moves page 2's start from 12 to 23); and says to check page 4 for evidence the old labels miss.

**Common wrong answers:**
- [ ] "The id stays, because nothing old changed": the id hashes the whole text, which is longer now.
- [ ] "Every row shifts by 40": text added at the end moves nothing before it.

**If you missed it, reread:** [short §5](../reading/C1_parsing.md#5-freeze-the-text-the-snapshot-id) · [short §4](../reading/C1_parsing.md#4-one-coordinate-system-the-page-table) · [lesson #snapshot](../lessons/C1_parsing.html#snapshot) · [lesson #offsets](../lessons/C1_parsing.html#offsets) · book Ch14 p.4/13

</details>
<!-- /q -->

<!-- q id=C1-A-03 type=A set=main -->
### C1-A-03 · Application (debugging)
**Question:** Find the three bugs in this loader.

```python
pages = [Page("climate", i, p.get_text().strip(), "pymupdf") for i, p in enumerate(doc)]
```

**Reply template:** `The bugs are ____, ____ and ____. The fixes are ____.`

<details><summary>Hint 1</summary>

Check each of the four fields against the v0 page record.

</details>

<details><summary>Hint 2</summary>

What does `enumerate` count from? What does `.strip()` delete? What is missing from the parser string?

</details>

<details><summary>Hint 3</summary>

On Corpus D, `.strip()` on every page removes 70 characters.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
1. page = i           enumerate counts from 0          → i + 1
2. .strip()           removes 70 characters on D       → keep the raw get_text()
                      (offsets and the text hash no longer match the parser's output)
3. "pymupdf"          no version                       → f"pymupdf {pymupdf.VersionBind}"  = "pymupdf 1.26.7"
```

**Key points** (a 3 needs every point):
- [ ] The page number is 0-based; use `i + 1`.
- [ ] `.strip()` changes the text (70 characters on Corpus D), so offsets and the hash change.
- [ ] The parser string has no version.

**For a 4, also:**
- [ ] Gives the check that catches each: `assert pages[0].page == 1`; the text hash or `snapshot_id` must equal `ea07572562ac`; the parser string must carry the version. Notes that LangChain's PDF loaders make bugs 1 and 2 by default (PyPDFLoader's 72,523 characters = the per-page `.strip()`).

**Common wrong answers:**
- [ ] "`.strip()` is fine, it only removes whitespace": whitespace is characters, and every later offset moves.
- [ ] "`enumerate` starts at 1": it starts at 0 unless you pass `start=1`.

**If you missed it, reread:** [short §3](../reading/C1_parsing.md#3-one-record-per-page-numbered-from-1) · [short §5](../reading/C1_parsing.md#5-freeze-the-text-the-snapshot-id) · [lesson #records](../lessons/C1_parsing.html#records) · book Ch14 p.5/13

</details>
<!-- /q -->

<!-- q id=C1-A-04 type=A set=main -->
### C1-A-04 · Application (offset shift)
**Question:** A page has two `ﬁ` ligatures, at raw offsets 100 and 300; after each is decomposed into `fi`, where does the character at raw offset 500 land?

**Reply template:** `It lands at ____, because ____.`

<details><summary>Hint 1</summary>

How many characters does one `ﬁ` become?

</details>

<details><summary>Hint 2</summary>

Only changes before offset 500 can move it. How many are there, and what does each add?

</details>

<details><summary>Hint 3</summary>

Each decomposed ligature adds 2 − 1 = 1 character.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** At 502: each of the two ligatures before it grows from one character to two, so it moves by +1 twice. The map back to raw keeps the link:

```
cleaned 100, 101  ← raw 100     (the ligature's two letters)
cleaned 102       ← raw 101
cleaned 502       ← raw 500
toy page: 520 characters → 522
```

**Key points** (a 3 needs every point):
- [ ] 502.
- [ ] Each decomposed ligature before the offset adds 1.
- [ ] The map: cleaned 502 ← raw 500.

**For a 4, also:**
- [ ] Self-checks: the whole page grows 520 → 522, and a character between the ligatures (raw 200) lands at 201; then says why this matters: a label `[500, 510)` written on the raw text would point two characters too early.

**Common wrong answers:**
- [ ] "500, characters do not move": the text before it got longer.
- [ ] "504, each ligature adds 2": one character is replaced by two, so the net change is +1.

**If you missed it, reread:** [short §8](../reading/C1_parsing.md#8-normalisation-moves-every-later-offset) · [short §9](../reading/C1_parsing.md#9-cleaning-as-logged-edits-and-why-v0-applies-none) · [lesson #unicode](../lessons/C1_parsing.html#unicode) · book Ch1 p.5/14

</details>
<!-- /q -->

<!-- q id=C1-A-05 type=A set=main -->
### C1-A-05 · Application (a logged edit)
**Question:** Plan rule R2's edit for the page text below, and give the cleaned → raw map.

```
page text:  "the accu-\nracy rose\n"        (20 characters; "accuracy" occurs on another page)
```

**Reply template:** `Edit: delete [____, ____) = ____. Cleaned text: ____. Map: cleaned i ← raw ____ for i < ____, raw ____ for i ≥ ____.`

<details><summary>Hint 1</summary>

R2 deletes only the hyphen and the newline, and only when the joined word occurs elsewhere.

</details>

<details><summary>Hint 2</summary>

Count: "the " is 4 characters, "accu" 4 more. At which offset is the hyphen?

</details>

<details><summary>Hint 3</summary>

The hyphen is at 8 and the newline at 9.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
edit      {page, rule: "R2", start: 8, end: 10, before: "-\n", after: ""}
cleaned   "the accuracy rose\n"            18 characters = 20 − 2
map       cleaned i ← raw i        for i < 8
          cleaned i ← raw i + 2    for i ≥ 8       e.g. cleaned 8 ("r") ← raw 10
undo      re-insert "-\n" at 8     → the raw text exactly
```

**Key points** (a 3 needs every point):
- [ ] The edit deletes [8, 10) = `"-\n"` only.
- [ ] Cleaned text `"the accuracy rose\n"`.
- [ ] Map: raw i for i < 8, raw i + 2 for i ≥ 8.

**For a 4, also:**
- [ ] Self-checks (20 − 2 = 18 characters; undo(apply) gives the raw text) and states the rule's limit: R2 leaves `"mar-\ngin"` alone when "margin" occurs nowhere else, and a naive join would damage real compounds (7 of 7 on Corpus D).

**Common wrong answers:**
- [ ] "Delete just the hyphen": the newline stays inside the word, `"accu\nracy"`.
- [ ] "Replace `-\n` with a space": that makes two words, "accu racy".

**If you missed it, reread:** [short §9](../reading/C1_parsing.md#9-cleaning-as-logged-edits-and-why-v0-applies-none) · [lesson #cleaning](../lessons/C1_parsing.html#cleaning) · book Ch1 p.5/14 (the book's cleaning step, with no log)

</details>
<!-- /q -->

<!-- q id=C1-T-01 type=T set=main -->
### C1-T-01 · Transfer
**Question:** A colleague's slide decks are exported to PDF, and many slides are pictures with a few words on top: what do you check first?

**Reply template:** `I would check ____, because ____. I would measure whether it matters by ____.`

<details><summary>Hint 1</summary>

What does a parser return for a page that is mostly a picture?

</details>

<details><summary>Hint 2</summary>

Which per-page counts separate a text slide from a picture slide? And which questions would be hurt if the picture's content is missing?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**
1. **Per-page counts:** characters and images on every slide. Flag image-only slides (0 characters, images > 0) and near-empty ones (a few words over a big image). Text drawn inside a picture is invisible to a text extractor.
2. **Reading order:** slides are built from text boxes, so the order follows the file. Read a sample of slides next to their extracted text.
3. **Does it matter:** count the eval questions whose evidence lies on flagged slides. Compare retrieval (Hit@k, CE@k) on those questions with the rest, and keep answer quality as a separate measurement.
4. **Trade-off:** OCR or image captioning (S2) costs more and brings its own errors. The book calls captioning overkill when the parser already gives the content as text (Ch16 p.10/11).

**Key points** (a 3 needs every point):
- [ ] Characters and images per page; flag image-only and near-empty slides.
- [ ] Check reading order on a sample of slides by eye.
- [ ] Measure it through questions: retrieval on the questions whose evidence is on flagged slides vs the rest, separate from answer quality.

**For a 4, also:**
- [ ] Names the trade-off and when not to act: OCR or captioning adds cost and new errors, so skip it if no question needs the picture content (Ch16 p.10/11).

**Common wrong answers:**
- [ ] "Run OCR on every slide first": that adds cost and errors before you know any question needs it.
- [ ] "An empty string means a blank slide": it can be a slide that is one picture; count the images.

**If you missed it, reread:** [short §2](../reading/C1_parsing.md#2-what-a-pdf-page-really-is) · [short §11](../reading/C1_parsing.md#11-measuring-parse-quality-in-three-separate-steps) · [lesson #page](../lessons/C1_parsing.html#page) · [lesson #measure](../lessons/C1_parsing.html#measure) · book Ch16 p.1/11 and p.10/11

</details>
<!-- /q -->

<!-- q id=C1-T-02 type=T set=main -->
### C1-T-02 · Transfer
**Question:** A results table in a two-column paper comes out one cell per line: what do you check, and how do you know whether it matters?

```
extracted text around the table (first cells):
Method
NQ
TQA
SQuAD
BM25
59.1
...
```

**Reply template:** `First I check ____. To know whether it matters, I ____. I keep ____ separate.`

<details><summary>Hint 1</summary>

The numbers are all there. What is lost when every cell is on its own line?

</details>

<details><summary>Hint 2</summary>

Which questions could be hurt by this page, and how would you compare v0 with a table-aware version on exactly those questions?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**
1. **The extraction itself.** Put the extracted text next to the rendered page. The cells are present, but the links between row and column are gone: nothing says which number belongs to which method and dataset. Check table detection: by ruling lines it finds nothing on an unruled table, and the text strategy over-detects (23 × 9 cells on the toy paper page, swallowing the page's text). So flag the page as a "suspected flattened table" (many short number lines, no table found) and check the reading order around it.
2. **Does it matter for retrieval?** Only if questions need the table. Find the eval questions whose gold spans lie in it. Build a comparison arm that keeps the table's structure (for example a layout parser, or tables written as Markdown), as its own snapshot with its own `snapshot_id`, and re-validate the spans. Compare Hit@k and CE@k on those questions, v0 vs the arm, and separately on the rest.
3. **Answer quality is separate.** Even when the right chunk is retrieved, the generator may pair a number with the wrong row; measure that later, on its own.

External context: rule-based table detection is weak on scientific pages (PyMuPDF F1 0.179, Table Transformer 0.913, [C1-3]).

**Key points** (a 3 needs every point):
- [ ] Compare the text with the rendered page: the cells survive, the row and column links do not.
- [ ] Table detection is unreliable here (ruling lines find 0 on an unruled table; the text strategy over-detects); flag the page.
- [ ] It matters only through the questions whose evidence is in the table: compare Hit@k / CE@k on them, v0 vs a table-aware arm with its own snapshot.
- [ ] Answer quality is measured separately from retrieval.

**For a 4, also:**
- [ ] Adds evidence and when not to act: benchmark numbers for table detection are external and belong to their own pages; if no question touches the table, leave v0 as it is.

**Common wrong answers:**
- [ ] "All the numbers are in the text, so it is fine": without rows and columns nobody can tell which number belongs to which method.
- [ ] "Switch every paper to a layout parser, because a benchmark says it reads tables better": a benchmark score belongs to its own pages; run it as an arm and compare on your questions.

**If you missed it, reread:** [short §7](../reading/C1_parsing.md#7-the-artifact-catalogue-and-one-check-for-each) · [short §11](../reading/C1_parsing.md#11-measuring-parse-quality-in-three-separate-steps) · [short §10](../reading/C1_parsing.md#10-parsers-compared-what-the-extra-cost-buys) · [lesson #artifacts](../lessons/C1_parsing.html#artifacts) · [lesson #measure](../lessons/C1_parsing.html#measure) · book Ch1 p.13/14 (a table that comes out one cell per line) and Ch16 p.10/11

</details>
<!-- /q -->

<!-- q id=C1-R-06 type=R set=interview source=AIQ-04-Q16 -->
### C1-R-06 · Interview (Recall)
**Question:** "Everyone focuses on retrieval algorithms - what's actually the hardest part of building RAG over enterprise documents?" *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (Q16), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `The hardest part is ____, because ____. I would handle it by ____. On my own project I would also ____.`

<details><summary>Hint 1</summary>

Every later stage only sees the text that the first stage produced.

</details>

<details><summary>Hint 2</summary>

Order the parsing tools by cost. Then: how do you know a parser is good on *your* files, and what happens to your labels when you re-parse?

</details>

<details><summary>Show answer (write yours first)</summary>

The repository's answer (excerpt, verbatim, MIT License, Copyright (c) 2026 Om):

> **Parsing.** The dirty secret of enterprise RAG is that the corpus is PDFs, scanned contracts, PowerPoints, and Excel exports - and if the text extraction is garbage, every downstream stage (chunking, embedding, retrieval, generation) is garbage with perfect fidelity.
>
> The modern toolbox, in escalating cost order: fast text extractors (PyMuPDF/pdfplumber) for digital-native PDFs; layout-aware ML parsers and hosted document-AI services (e.g., unstructured, LlamaParse, Azure Document Intelligence, Reducto and similar) for structure; and **VLM-based parsing** - render each page to an image, have a vision-language model transcribe it to markdown - which handles brutal layouts and is increasingly the quality ceiling, at the price of an LLM call per page.
>
> Practical advice you should volunteer: sample and eyeball parsed output before optimising anything else; build per-document-type parsing paths; keep raw originals so you can re-parse when tooling improves; and route by document difficulty (cheap parser for clean PDFs, VLM for the nasty 10%). Budget-wise, expect parsing to consume more engineering time than embedding, indexing, and prompting combined.

**Our check of that answer:** the core is right and matches C1: extraction errors flow into every later stage, the tools come in cost order, and you look at parsed pages before tuning anything. Three corrections:
1. "The nasty 10%" and "more engineering time than ... combined" have no source. Keep the advice; drop the numbers until you measure them.
2. "VLMs are increasingly the quality ceiling" depends on the pages. On OmniDocBench's English pages (external, [C1-2]), a layout pipeline had a lower text edit distance (MinerU 0.061) than GPT-4o (0.144). Route by page difficulty, but test each route.
3. Two things are missing. **Measure on your own corpus:** a benchmark score belongs to its own pages. **Freeze the snapshot:** re-parsing gives new text, so it is a new `snapshot_id`, and every label must be rebound to it.

**Model answer:** Parsing. The corpus is PDFs, scans and slides, and every later stage sees only the extracted text, so extraction errors flow into chunking, embedding, retrieval and the answer. Typical failures: columns read in the wrong order, tables flattened into one cell per line, headers and footers repeated in every chunk, scanned pages with no text layer. Handle it in cost order: a fast text extractor for born-digital pages, a layout model for tables and hard layouts, a vision model per page only for the worst pages. Route pages by difficulty, and check parse quality per page before indexing. Two habits on top: measure the parser on your own corpus, with per-page signals, a hand-checked sample and questions on the affected pages; and freeze the extracted text as a snapshot with an id, so any re-parse is a recorded new snapshot and the labels are rebound to it.

**Key points** (a 3 needs every point):
- [ ] Parsing is the hard part: every later stage sees only the extracted text.
- [ ] Names typical failures (columns, tables, headers/footers, scanned pages).
- [ ] Tools in cost order (text extractor → layout model → VLM per page), routed by page difficulty, with a quality check before indexing.
- [ ] Measure on your own corpus; a benchmark score does not transfer.
- [ ] Freeze the snapshot: a re-parse is a new `snapshot_id`, and labels are rebound.

**For a 4, also:**
- [ ] Corrects the repo's answer with evidence: "10%" and the engineering-time claim are unsourced, and on OmniDocBench's English pages a layout pipeline beat GPT-4o on text (0.061 vs 0.144 edit distance, external).

**Common wrong answers:**
- [ ] "The embedding model or the retrieval algorithm": they work only on the text the parser produced.
- [ ] "Pick the parser that tops a public benchmark and you are done": its score belongs to its own pages; measure on yours.

**If you missed it, reread:** [short §10](../reading/C1_parsing.md#10-parsers-compared-what-the-extra-cost-buys) · [short §11](../reading/C1_parsing.md#11-measuring-parse-quality-in-three-separate-steps) · [short §5](../reading/C1_parsing.md#5-freeze-the-text-the-snapshot-id) · [lesson #parsers](../lessons/C1_parsing.html#parsers) · [lesson #measure](../lessons/C1_parsing.html#measure) · book Ch1 p.4/14

</details>
<!-- /q -->
