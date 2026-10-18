<!-- kit:questions concept=I2 version=1 -->
# I2 questions: structure-aware chunking (headings from typography, section tree, balanced split, invariants)

**How to use:** write your answer and a confidence (1–3) first. Then open the answer and tick the key points you really wrote.

**Where the numbers come from:** `sources/verification/I2/i2_measure.py` on the climate PDF (Corpus D) with PyMuPDF 1.26.7, snapshot `ea07572562ac` ([I2_FACTS](../../sources/verification/I2/I2_FACTS.md) S1–S14; [the run](../../sources/verification/I2/out_i2_measure.txt)). The 8 answerable draft questions (D-001…D-008) are LLM-drafted and not yet checked by you: ranks and CE on them are observations, not results. "Toy" data is made up; "formula" numbers are computed in the answer. The book pages are listed per 04/07 and were not re-opened in this session. No API was called to write this file.

<!-- q id=I2-PRE-01 type=R set=pre -->
### I2-PRE-01 · Recall (before reading)
**Question:** A chunker cuts each PDF page on its own. What can go wrong where one page ends and the next begins?

**Reply template:** `A ____ can be separated from ____, and a ____ can be ____.`

<details><summary>Hint 1</summary>

Think about what usually sits at the bottom of a page, and what continues at the top of the next one.

</details>

<details><summary>Hint 2</summary>

Two things can straddle a page break: a heading and its text, and a single sentence.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The chunk ends wherever the page ends. A **heading** at the bottom of a page lands in one chunk and its **paragraph** in the next (an orphaned heading), and a **sentence** that runs over the break is cut in two, so no chunk holds it whole. On the climate PDF (S8, S12):

```
orphaned headings                16   e.g. "Coal", the last line of page 1; its paragraph starts page 2
sentences cut by a page break     8   e.g. the PPP sentence, pages 12→13
```

**Key points** (a 3 needs every point):
- [ ] A heading can be separated from the text it introduces (orphaned at the end of a page).
- [ ] A sentence can be cut in two at the page break, so no chunk holds it whole.

**For a 4, also:**
- [ ] Names the fix: cut at headings and let a section run across the page break, keeping exact offsets (and page pieces for citations).

**Common wrong answers:**
- [ ] "Nothing, the 200-character overlap covers it": in a per-page chunker the overlap repeats text inside one page; it never reaches across the break.
- [ ] "Only that the last chunk of a page is shorter": the problem is what the cut separates, not the length.

**If you missed it, reread:** [short §1](../reading/I2_structure_chunking.md#1-the-failure-a-heading-at-the-bottom-of-a-page) · [lesson #s1](../lessons/I2_structure_chunking.html#s1) · book Ch7 p.1–2/11 (per 07; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-PRE-02 type=R set=pre -->
### I2-PRE-02 · Recall (before reading)
**Question:** A PDF's text has no Markdown or HTML tags. How could a program still tell which lines are headings?

**Reply template:** `It can read ____ for each piece of text; a heading is ____ or ____.`

<details><summary>Hint 1</summary>

How do *you* spot a heading on a printed page at a glance?

</details>

<details><summary>Hint 2</summary>

The plain text has lost the styling. Which PyMuPDF output keeps it?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** From the typography, which PyMuPDF keeps in `page.get_text("dict")`: every span has a font **size** and style **flags**. A heading line is **larger than the body text**, or **bold at the body size**; it is also short and does not end with a full stop. If the PDF has an outline (bookmarks, `doc.get_toc()`), that is an even better first source. On the climate PDF size alone finds 90 headings and size + bold finds 282 (S4).

**Key points** (a 3 needs every point):
- [ ] Use per-span font information (size, bold flag), not the plain text.
- [ ] A heading is larger than the body text, or bold at the body size.

**For a 4, also:**
- [ ] Adds the outline as the first source when present, or the filters (short line, no final full stop, not repeated on every page).

**Common wrong answers:**
- [ ] "Look for lines that start with #": a PDF's text has no Markdown.
- [ ] "Headings are always the bigger text": on the climate PDF 192 of 282 headings are bold at body size (S4).

**If you missed it, reread:** [short §2](../reading/I2_structure_chunking.md#2-inside-the-pdf-blocks-lines-spans-and-the-bold-bit) · [short §4](../reading/I2_structure_chunking.md#4-headings-size-alone-misses-two-thirds-of-them) · [lesson #s2](../lessons/I2_structure_chunking.html#s2) · book Ch7 p.1–2/11 (nearest page; per 07; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-R-01 type=R set=main -->
### I2-R-01 · Recall
**Question:** Which span-dict field and which bit tell you a span is bold?

**Reply template:** `field ____, bit value ____; test: ____.`

<details><summary>Hint 1</summary>

One integer field packs several yes/no style facts, one bit each.

</details>

<details><summary>Hint 2</summary>

The bits are 1, 2, 4, 8 and 16. Which one is bold, and how do you test one bit of a number?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The `flags` field, bit value **16**. Test it with a bitwise AND, because `flags` holds several bits at once:

```
bold(span) = (flags & 16) != 0  or  (char_flags & 8) != 0
title span (S2):  flags 20 = 16 bold + 4 serif   → bold
body span (S2):   flags 4  = serif only           → not bold
```

Bit 16 comes from the font's metadata; synthetic bold shows up in bit 8 of `char_flags`, so the course (like `pymupdf4llm`) checks both.

**Key points** (a 3 needs every point):
- [ ] The field is `flags`.
- [ ] Bold is the bit with value 16.
- [ ] Test it with a bitwise AND (`flags & 16`), not equality.

**For a 4, also:**
- [ ] Adds `char_flags & 8` for synthetic bold, with the reason (bit 16 comes from font metadata), or decodes 20 = 16 + 4.

**Common wrong answers:**
- [ ] "`flags == 16`": the title's flags are 20 (bold + serif), so equality misses it.
- [ ] "Check whether the font name contains 'Bold'": a guess that works on this PDF's font names, not the flag PyMuPDF sets.

**If you missed it, reread:** [short §2](../reading/I2_structure_chunking.md#2-inside-the-pdf-blocks-lines-spans-and-the-bold-bit) · [lesson #s2](../lessons/I2_structure_chunking.html#s2) · book Ch7 p.1–2/11 (nearest page; no chapter teaches span flags; per 07; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-R-02 type=R set=main -->
### I2-R-02 · Recall
**Question:** Why is the body font size estimated by character count, not by span count?

**Reply template:** `Because a span count measures ____, while a character count measures ____.`

<details><summary>Hint 1</summary>

What is the body size supposed to describe: how often the style changes, or how much text is set in a size?

</details>

<details><summary>Hint 2</summary>

Think of blank spans, and of a page full of short labels.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The body size should be the size in which **most of the text** is set, because every heading level is defined relative to it. A span count measures how often the style changes: blank spans count but hold no text, and short labels or table cells make many tiny spans. Counting characters measures the amount of text directly (S3):

```
12 pt regular   63,762 characters (90.6%)   → body size 12.0
11.04 pt        0 characters (blank Calibri spans)
spans: 1,006 at 12.0, 68 at 13.56            (here both agree; on a different file they may not)
```

**Key points** (a 3 needs every point):
- [ ] The body size is the size that holds the most text.
- [ ] A span count measures style changes or fragments (blank and tiny spans count as much as long ones).
- [ ] Characters measure how much text is set in each size.

**For a 4, also:**
- [ ] Says why it matters: the body size anchors every level (larger = heading level, bold at body size = the next level), so a wrong body size shifts all of them.

**Common wrong answers:**
- [ ] "They always give the same answer": they agree on this PDF, but nothing guarantees it.
- [ ] "Take the smallest size": the smallest size here is blank Calibri spans with 0 characters.

**If you missed it, reread:** [short §3](../reading/I2_structure_chunking.md#3-the-body-size-count-characters-not-spans) · [lesson #s3](../lessons/I2_structure_chunking.html#s3) · book Ch7 p.1–2/11 (nearest page; per 07; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-R-03 type=R set=main -->
### I2-R-03 · Recall
**Question:** Why can a structure-aware chunk contain its own heading but not its parent headings?

**Reply template:** `Because a chunk is ____; its own heading ____, but its parents' headings ____. The parents go into ____.`

<details><summary>Hint 1</summary>

What must `doc_text[a:b]` equal for every chunk?

</details>

<details><summary>Hint 2</summary>

Where in the document does a section's own heading sit, and where does its chapter heading sit?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** A chunk is an **exact slice** `[a, b)` of the frozen snapshot: `doc_text[a:b] == text`. A section's own heading sits at the start of its section, so it is inside the slice (a heading glues forward into its text). The chapter and higher headings sit **earlier in the document**, outside the slice; pasting them into the chunk text would break the round trip, and with it span gold and page citations. So the full path goes into metadata (`section_path`). Putting the path into the embedded text is I5's experiment, kept apart so that v1.1 changes one thing.

**Key points** (a 3 needs every point):
- [ ] A chunk is an exact slice of the snapshot (offset round trip).
- [ ] Its own heading lies inside its range; the parent headings lie earlier, outside it.
- [ ] The parent path is stored as metadata (`section_path`) instead.

**For a 4, also:**
- [ ] Names the limit: prepending the path for embedding is I5's separate experiment, and a second piece of a split section (e.g. L3 chunk 65) does not even start with its section heading, so the metadata path is what identifies it.

**Common wrong answers:**
- [ ] "Parents are left out to save tokens": they are left out to keep exact offsets.
- [ ] "Just paste the breadcrumb at the top of each chunk": that breaks `doc_text[a:b] == text` and changes a second variable (I5).

**If you missed it, reread:** [short §7](../reading/I2_structure_chunking.md#7-the-section-tree-and-the-breadcrumb) · [short §11](../reading/I2_structure_chunking.md#11-the-invariants-that-protect-span-gold) · [lesson #s7](../lessons/I2_structure_chunking.html#s7) · book Ch7 p.8/11 (per 04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-R-04 type=R set=main -->
### I2-R-04 · Recall
**Question:** What does a Markdown header splitter lose that the course chunker keeps?

**Reply template:** `It loses ____ and ____; the course chunker keeps ____, so ____.`

<details><summary>Hint 1</summary>

Compare a splitter's output text with the snapshot, character by character.

</details>

<details><summary>Hint 2</summary>

Three things: what happens to the lines, to the heading, and to the length.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** LangChain's `MarkdownHeaderTextSplitter` (from its source, not run here) strips every line and re-joins lines with `"  \n"`, so its chunks are **rewritten text with no offsets into the snapshot**. With the default `strip_headers=True` the heading leaves the chunk text and survives only as metadata, and there is **no size cap**. Before it, a PDF → Markdown converter such as `pymupdf4llm` finds headers by size only, so on the climate PDF it would miss the 192 bold sub-headings. The course chunker keeps **exact slices** `[a, b)`, so span gold (CE@k) and page citations work without mapping each chunk back.

**Key points** (a 3 needs every point):
- [ ] Offsets: the splitter rewrites the text, so its chunks are not exact slices of the snapshot.
- [ ] Consequence: span gold and page citations cannot use them until each chunk is re-anchored to the snapshot, which can fail; the course chunker's exact slices need no such step.

**For a 4, also:**
- [ ] Two more losses: by default the heading is removed from the chunk text (metadata only), and there is no size cap; or: the converter's size-only headers miss the bold sub-headings.

**Common wrong answers:**
- [ ] "Nothing, it is the same text in Markdown form": whitespace and line structure are rewritten, so offsets no longer match.
- [ ] "It loses the heading path": it keeps the headings, as metadata; what it loses is the offsets.

**If you missed it, reread:** [short §6](../reading/I2_structure_chunking.md#6-aligning-every-heading-to-the-snapshot) · [lesson #s6](../lessons/I2_structure_chunking.html#s6) · book Ch7 p.8/11 (nearest page; per 04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-R-05 type=R set=main -->
### I2-R-05 · Recall
**Question:** On the climate PDF, which two page-break failures does per-page chunking cause, and how does a structure chunk that crosses a page still cite the right pages?

**Reply template:** `____ (count ____) and ____ (count ____). A crossing chunk keeps ____.`

<details><summary>Hint 1</summary>

One failure involves a heading, the other a sentence. Think of "Coal" and the PPP sentence.

</details>

<details><summary>Hint 2</summary>

A chunk has one range `[a, b)`. What extra list lets it name each page it touches?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
orphaned headings        16   "Coal" is the last line of page 1; its paragraph starts page 2 (S8)
mid-sentence cuts         8   the PPP sentence runs pages 12→13
L3 structure chunks: "Coal" + first body line in chunk 3 (pages 1–2); PPP sentence whole (S12)
```

A structure chunk may run across a page break; 27 of the 117 L3 chunks do. It keeps one exact range `[a, b)` plus `page_segments`, a list of `(page, a, b)` pieces that together rebuild the range, so it can cite both pages exactly.

**Key points** (a 3 needs every point):
- [ ] 16 orphaned headings (a heading ends the page, its text is on the next).
- [ ] 8 sentences cut at a page break.
- [ ] A crossing chunk stores `page_segments` (page, a, b) that rebuild `[a, b)`, so it cites every page it touches.

**For a 4, also:**
- [ ] Notes that the cross-page control also keeps the PPP sentence whole: page scope alone repairs cuts, so v1.1 must be compared with that control, not only with per-page v0.

**Common wrong answers:**
- [ ] "Raise the overlap": a per-page chunker's overlap never crosses the page break.
- [ ] "Structure chunks must stop at page breaks, or citations break": `page_segments` keep citations exact across pages.

**If you missed it, reread:** [short §1](../reading/I2_structure_chunking.md#1-the-failure-a-heading-at-the-bottom-of-a-page) · [short §10](../reading/I2_structure_chunking.md#10-continuation-across-pages) · [lesson #s1](../lessons/I2_structure_chunking.html#s1) · [lesson #s10](../lessons/I2_structure_chunking.html#s10) · book Ch7 p.1–2/11 (per 07; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-R-06 type=R set=main -->
### I2-R-06 · Recall
**Question:** Why are headings found in the snapshot with a cursor that only moves forward, and why does the search stop when one is not found?

**Reply template:** `A forward cursor stops ____. Stopping on a miss prevents ____.`

<details><summary>Hint 1</summary>

What does `doc_text.find("Paris Agreement")` return when the title occurs twice?

</details>

<details><summary>Hint 2</summary>

If one heading were skipped, what would happen to the two sections around it, and who would notice?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** The `dict` output has fonts but no offsets; the snapshot has offsets but no fonts. They line up because the `dict` lines plus `"\n"` rebuild `page.get_text()` exactly (33 of 33 pages, S5). Searching from offset 0 returns the **first** match: the page 23 "Paris Agreement" would land on page 10, and "Coal" also occurs in body text. Searching from the end of the previous heading keeps each match in reading order. If a heading is not found, the program **stops** (fails closed): a silently skipped heading would merge two sections, and nothing later would notice. Result: 282 of 282 aligned; "Coal" at `[2418, 2423)`, page 1 ending at 2424 (S6).

**Key points** (a 3 needs every point):
- [ ] Titles repeat (11 repeated titles) and heading words occur in body text, so a search from the start finds the wrong place.
- [ ] The cursor moves forward from the previous heading's end, keeping reading order.
- [ ] Failing closed: a missed heading would silently merge two sections.

**For a 4, also:**
- [ ] Says why alignment is possible at all: the `dict` lines rebuild the plain page text exactly (33 of 33 pages), and gives the result (282 of 282).

**Common wrong answers:**
- [ ] "Titles are unique, so a search from the start is fine": 11 titles repeat on this PDF.
- [ ] "Skip the few headings that are not found": each skip merges two sections without any error.

**If you missed it, reread:** [short §6](../reading/I2_structure_chunking.md#6-aligning-every-heading-to-the-snapshot) · [short §5](../reading/I2_structure_chunking.md#5-error-modes-and-titles-that-repeat) · [lesson #s6](../lessons/I2_structure_chunking.html#s6) · book Ch7 p.8/11 (nearest page; per 04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-R-07 type=R set=main -->
### I2-R-07 · Recall
**Question:** At split level L3, size-only and size + bold heading detection give the same 117 chunks on the climate PDF. So why keep the bold rule?

**Reply template:** `At L3 the boundaries come from ____, which both rules find. The bold rule matters for ____ and ____.`

<details><summary>Hint 1</summary>

Which level are the 192 headings that only the bold rule finds?

</details>

<details><summary>Hint 2</summary>

Where else is a heading used besides as a chunk boundary?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** At L3 a new chunk starts only at headings of level 3 or higher (title, chapters, 13.56-point sections), and both rules find all of those. The 192 headings only the bold rule finds are **L4 sub-sections**, which stay inside an L3 chunk (S9). They matter when you **split at L4** (209 chunks, or 139 with merging), and for the **breadcrumb**: without them the path stops at the section, so the two "Paris Agreement" sub-sections disappear from the paths. On a different corpus the bold headings may sit at the level you split at.

**Key points** (a 3 needs every point):
- [ ] The L3 boundaries are the 13.56-point sections (and higher), which size-only also finds.
- [ ] The 192 bold-only headings are L4 sub-sections; they stay inside L3 chunks.
- [ ] They matter for splitting at L4 and for the section path.

**For a 4, also:**
- [ ] Generalises with a check: on another corpus the bold headings may be at the split level, so keep both detectors as arms and compare their counts per level.

**Common wrong answers:**
- [ ] "Then the bold rule is useless": it changes the L4 arm and every sub-section's path.
- [ ] "Size-only must give fewer chunks, since it finds fewer headings": the missing headings are below the split level.

**If you missed it, reread:** [short §8](../reading/I2_structure_chunking.md#8-choosing-the-split-level) · [short §4](../reading/I2_structure_chunking.md#4-headings-size-alone-misses-two-thirds-of-them) · [lesson #s8](../lessons/I2_structure_chunking.html#s8) · [lesson #s4](../lessons/I2_structure_chunking.html#s4) · book Ch9 p.10–11/14 (per 02/04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-R-08 type=R set=main -->
### I2-R-08 · Recall
**Question:** What does the 10-chunk eye inspection check, and why does it come before any retrieval metric?

**Reply template:** `It checks ____ on 10 chunks chosen by ____. It comes first because ____.`

<details><summary>Hint 1</summary>

How are the 10 chunks picked so that you cannot choose the nice ones?

</details>

<details><summary>Hint 2</summary>

If a heading rule were wrong, what would it look like in a CE@4 table?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Ten chunks drawn with a fixed seed (`random.Random(0).sample`), each checked against a sheet: starts at a heading or a clean continuation, ends at a sentence end, right path, no heading stranded at the end, right pages. It comes first because a parsing error shows up in a metric as a retrieval miss, which you would blame on the retriever. Rule of thumb ([P]): fewer than 8 of 10 pass → fix the rules before measuring. On D (S13):

```
chunks 5, 33, 49, 51, 53, 62, 65, 97, 108, 113
10 of 10 start at a heading and end at a sentence end
65 and 108: second pieces, starting at a sub-heading · 51, 62, 97, 108 cross a page break
```

**Key points** (a 3 needs every point):
- [ ] A random sample with a fixed seed (no hand-picking), 10 chunks.
- [ ] Checks: start at a heading or clean continuation, sentence end, correct path, pages.
- [ ] Before metrics, because parsing errors would look like retrieval misses.

**For a 4, also:**
- [ ] Gives the decision rule (fewer than 8 of 10 → fix first) or the D result (10 of 10; your own verdict sheet is still to do in the notebook).

**Common wrong answers:**
- [ ] "Pick 10 chunks that look interesting": that hides the typical errors; use a fixed seed.
- [ ] "The metrics will catch parsing errors anyway": they show a miss, not its cause.

**If you missed it, reread:** [short §12](../reading/I2_structure_chunking.md#12-eye-inspection-before-any-metric) · [lesson #s12](../lessons/I2_structure_chunking.html#s12) · book Ch7 p.1–2/11 (nearest page; per 07; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-A-01 type=A set=main -->
### I2-A-01 · Application
**Question:** Assign a heading level (or "not a heading") to each line below. Body size is 12; the only bold sizes above it are 18 and 13.56.

| # | Size | Bold? | Text |
|---|---|---|---|
| 1 | 18 | yes | Chapter 3: Energy Storage |
| 2 | 13.56 | yes | Batteries |
| 3 | 12 | yes | Grid-Scale Batteries |
| 4 | 12 | no | Large batteries store surplus power for later use. |
| 5 | 12 | yes | Cost matters most. |
| 6 | 12 | yes | Energy Storage Review (this line is at the top of every page) |

(toy data)

**Reply template:** `1 → ____, 2 → ____, 3 → ____, 4 → ____, 5 → ____, 6 → ____`

<details><summary>Hint 1</summary>

Rank the bold sizes above the body size, largest first. Then: what level does an all-bold line at the body size get?

</details>

<details><summary>Hint 2</summary>

Apply the three filters to every candidate: word count, final punctuation, repeated on 3 or more pages.

</details>

<details><summary>Hint 3</summary>

18 → level 1 and 13.56 → level 2 in this document. So bold at size 12 is level 3. Now check lines 5 and 6 against the filters.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
1  18, bold            → level 1 (largest bold size)
2  13.56, bold         → level 2
3  12, bold, short     → level 3 (bold at body size = the next level)
4  12, regular         → body text
5  12, bold, ends "."  → not a heading (final full stop: a bold sentence)
6  12, bold, on every page → not a heading (running header: on 3 or more pages)
```

Levels come from this document's size ranks, not from Corpus D's numbering. Self-check with size only: lines 1 and 2 stay, line 3 is lost, the same kind of loss as 192 of 282 on Corpus D.

**Key points** (a 3 needs every point):
- [ ] 1 → level 1 and 2 → level 2, by size rank.
- [ ] 3 → level 3: all bold at the body size gets the next level.
- [ ] 4 → body text.
- [ ] 5 and 6 → not headings (final full stop; running header on 3 or more pages).

**For a 4, also:**
- [ ] Self-check: says what size-only detection would give (line 3 missed), or counts headings per level and compares with what the page shows.

**Common wrong answers:**
- [ ] "Line 1 is level 2, because chapters are level 2 on Corpus D": levels come from this document's size ranks.
- [ ] "Line 5 is a heading because it is bold": a bold line ending in a full stop is a sentence.

**If you missed it, reread:** [short §4](../reading/I2_structure_chunking.md#4-headings-size-alone-misses-two-thirds-of-them) · [short §5](../reading/I2_structure_chunking.md#5-error-modes-and-titles-that-repeat) · [lesson #s4](../lessons/I2_structure_chunking.html#s4) · book Ch7 p.1–2/11 (nearest page; per 07; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-A-02 type=A set=main -->
### I2-A-02 · Application
**Question:** A section of 2,300 characters must be split with cap 1,000. Give the balanced split sizes, and say why not 1,000 + 1,000 + 300.

**Reply template:** `n = ____, pieces about ____ + ____ + ____. Not 1,000 + 1,000 + 300, because ____.`

<details><summary>Hint 1</summary>

First the number of pieces: the smallest n with every piece under the cap.

</details>

<details><summary>Hint 2</summary>

n = ⌈ℓ / C⌉, ideal length ℓ / n. Where does each real cut then move to?

</details>

<details><summary>Hint 3</summary>

n = ⌈2300 / 1000⌉ = 3. Now divide.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** (formula)

```
n = ⌈2300 / 1000⌉ = 3        ideal length 2300 / 3 ≈ 766.7
ideal cut points ≈ 767 and ≈ 1,533 → pieces about 767 + 767 + 766
each cut moves to the sentence-ending line break within half a piece (≈ 383) of its ideal point
```

Filling to the cap leaves a short tail and puts each cut wherever the 1,000th character falls, often mid-sentence. The balanced split gives near-equal pieces and chooses sentence ends. The real case on Corpus D (S10): a 1,004-character section → balanced 341 + 663; naive cap cutting 1,000 + 4.

**Key points** (a 3 needs every point):
- [ ] n = 3.
- [ ] Pieces of about 767 each (2,300 / 3), cut at sentence ends near those points.
- [ ] Not 1,000 + 1,000 + 300: uneven sizes with a short tail, and cuts not chosen at sentence ends.

**For a 4, also:**
- [ ] Self-check: the pieces add up to 2,300 and each is ≤ 1,000; real pieces are uneven because the cuts move to sentence ends (1,004 → 341 + 663).

**Common wrong answers:**
- [ ] "1,000 + 1,000 + 300 is fine, every piece fits the cap": the cap is met, but the tail is short and the cuts fall mid-sentence.
- [ ] "Two pieces of 1,150": each would be over the cap.

**If you missed it, reread:** [short §9](../reading/I2_structure_chunking.md#9-balanced-splitting-and-merging) · [lesson #s9](../lessons/I2_structure_chunking.html#s9) · book Ch14 p.4–5/13 (nearest page; per 04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-A-03 type=A set=main -->
### I2-A-03 · Application
**Question:** Which chunk below breaks the "no section crossing" property, and how would you fix it? No chunk is merged; cap 1,000.

```
sections at the split level:   S1 [0, 900)    S2 [900, 2100)    S3 [2100, 2600)
chunks:                        c1 [0, 900)    c2 [900, 1500)    c3 [1500, 2200)    c4 [2200, 2600)
```

(toy data)

**Reply template:** `Chunk ____ breaks it, because ____. Fix: ____.`

<details><summary>Hint 1</summary>

For each chunk, ask: does a section start strictly inside it?

</details>

<details><summary>Hint 2</summary>

A boundary inside a chunk is allowed only after a run of headings (glued) or in a merged chunk. Is c3 either?

</details>

<details><summary>Hint 3</summary>

S3 starts at 2100. Which chunk has a < 2100 < b?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **c3**: S3 starts at 2100, and 1500 < 2100 < 2200, so c3 holds the end of S2 and the start of S3. The text before 2100 is S2's body, not a run of headings, and c3 is not merged, so it is a real crossing. Fix: cut at the boundary.

```
c3 [1500, 2100)  600 chars      c4 [2100, 2600)  500 chars
self-check: c1…c4 tile [0, 2600) with no gap or overlap; all ≤ 1,000; each lies in one section
```

**Key points** (a 3 needs every point):
- [ ] c3 is the crossing chunk.
- [ ] Because the S3 boundary (2100) lies strictly inside it, after S2 body text.
- [ ] Fix: end c3 at 2100 and start c4 at 2100.

**For a 4, also:**
- [ ] Self-check: re-runs the other invariants after the fix (tiling with no gap, the cap) and names the two allowed exceptions (a glued heading run, a merged chunk).

**Common wrong answers:**
- [ ] "c4, because it does not start at a section start": a continuation piece may start inside a section.
- [ ] "None, every chunk is under the cap": the cap is a different invariant.

**If you missed it, reread:** [short §11](../reading/I2_structure_chunking.md#11-the-invariants-that-protect-span-gold) · [short §8](../reading/I2_structure_chunking.md#8-choosing-the-split-level) · [lesson #s11](../lessons/I2_structure_chunking.html#s11) · book Ch14 p.4–5/13 (nearest page; per 04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-A-04 type=A set=main -->
### I2-A-04 · Application
**Question:** Build the section path for the page 23 "Paris Agreement" sub-heading from these headings (Corpus D, in reading order; some headings in between are left out, none of which changes the answer).

```
L2  Chapter 15: Climate Change and Technology        page 22
L3  Digital Technologies                             page 22
L4  Smart Grids                                      page 22
L4  Internet of Things (IoT)                         page 23
L3  Carbon Capture and Utilization                   page 23
L4  Direct Air Capture (DAC)                         page 23
L2  Chapter 16: Global Cooperation and Governance    page 23
L3  International Agreements                         page 23
L4  Paris Agreement                                  page 23
```

**Reply template:** `path = ____ > ____ > ____`

<details><summary>Hint 1</summary>

Keep a stack of open headings. A new heading closes every open heading at its own level or deeper.

</details>

<details><summary>Hint 2</summary>

What happens to the stack when the Chapter 16 heading arrives?

</details>

<details><summary>Hint 3</summary>

At Chapter 16 (L2), pop everything at L2 or deeper. Then push L3 International Agreements.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
Chapter 16: Global Cooperation and Governance > International Agreements > Paris Agreement
```

The stack rule: pop while the top's level ≥ the new heading's level, then push. Chapter 16 (L2) pops Chapter 15 and everything under it; International Agreements (L3) and Paris Agreement (L4) are pushed on top. The document title (L1) sits above every path and is left off. Self-check against page 10 (S7): Chapter 6: Global and Local Climate Action > International Collaboration > Paris Agreement. Same leaf, different path: the path, not the title, identifies the section.

**Key points** (a 3 needs every point):
- [ ] The path is Chapter 16 > International Agreements > Paris Agreement.
- [ ] Uses the stack rule: a heading closes open headings at its level or deeper.

**For a 4, also:**
- [ ] Self-check: contrasts the page 10 path (Chapter 6 > International Collaboration > Paris Agreement) and says the path, not the leaf title, is the identity.

**Common wrong answers:**
- [ ] "Chapter 15 > Carbon Capture and Utilization > Paris Agreement": the Chapter 16 heading closed Chapter 15.
- [ ] "Chapter 6 > International Collaboration > Paris Agreement": that is the other Paris Agreement, on page 10.

**If you missed it, reread:** [short §7](../reading/I2_structure_chunking.md#7-the-section-tree-and-the-breadcrumb) · [short §5](../reading/I2_structure_chunking.md#5-error-modes-and-titles-that-repeat) · [lesson #s7](../lessons/I2_structure_chunking.html#s7) · book Ch7 p.8/11 (per 04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-A-05 type=A set=main -->
### I2-A-05 · Application
**Question:** For each case, say what the heading detector should do, and which rule does it.

```
(a) a chapter title in bold 18 pt whose last word wraps onto a second bold 18 pt line in the same block
(b) the bold line "Climate Brief" at the top of every page
(c) a whole line in bold at body size: "Emissions must fall by half."
(d) "International Agreements" is found as a sub-heading (L4) on page 6 and as a section (L3) on page 23
```

(a)–(c) toy; (d) Corpus D (S7)

**Reply template:** `(a) ____ (b) ____ (c) ____ (d) ____`

<details><summary>Hint 1</summary>

Three of the four are handled by a joining rule or a filter. One is not an error at all.

</details>

<details><summary>Hint 2</summary>

The filters: at most 12 words, no final `. ! ?`, not on 3 or more pages. The joining rule: consecutive heading lines of the same level in one block.

</details>

<details><summary>Hint 3</summary>

(a) is Corpus D's Chapter 5 case: 22 level-2 lines became 21 headings.

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:**

```
(a) join the two lines into one heading          rule: same level, consecutive, same block
(b) drop it                                       rule: a line on 3 or more pages is a running header
(c) drop it                                       rule: no final . ! ? (it is a bold sentence)
(d) keep both, each at its own level              not an error: the path tells them apart
```

On Corpus D, (a) is Chapter 5's title wrapping onto "Mitigation" (22 level-2 lines → 21 headings). For (d), the moving cursor gives each its own offset, and the paths differ: Chapter 4 > Climate Policy > International Agreements vs Chapter 16 > International Agreements.

**Key points** (a 3 needs every point):
- [ ] (a) join into one heading (same level, consecutive lines, one block).
- [ ] (b) drop: repeated on 3 or more pages (running header).
- [ ] (c) drop: ends with a full stop.
- [ ] (d) keep both: a repeated title is not an error; the path is the identity.

**For a 4, also:**
- [ ] Self-check: compares the heading count per level with what the document should have (21 chapters on Corpus D), or reads the 10-chunk inspection sheet.

**Common wrong answers:**
- [ ] "(a) gives two chapters": without joining, yes; that is the error the rule repairs.
- [ ] "(d) is a detection error, so merge or drop one": both are real headings in different chapters.

**If you missed it, reread:** [short §5](../reading/I2_structure_chunking.md#5-error-modes-and-titles-that-repeat) · [short §4](../reading/I2_structure_chunking.md#4-headings-size-alone-misses-two-thirds-of-them) · [lesson #s5](../lessons/I2_structure_chunking.html#s5) · book Ch7 p.1–2/11 (nearest page; per 07; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-A-06 type=A set=main -->
### I2-A-06 · Application
**Question:** Split level L4, min-chars 400, cap 1,000. Which of these adjacent units get merged?

```
unit  parent (L3)                          length
A     National Strategies                   290
B     National Strategies                   295
C     National Strategies                   307
D     Local and Community Initiatives       362
```

(the lengths are Corpus D's Chapter 6 sub-sections, S7; treating them as units is a toy)

**Reply template:** `Merged: ____. Not merged: ____ because ____.`

<details><summary>Hint 1</summary>

Three conditions for a pair: both under min-chars, same parent, together within the cap.

</details>

<details><summary>Hint 2</summary>

The rule repeats from the start after every merge. Is the merged unit still under 400?

</details>

<details><summary>Hint 3</summary>

A + B: 290 + 295 = 585. Now test the pair (A+B, C), then (C, D).

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** (formula)

```
A + B: both < 400, same parent, 585 ≤ 1,000      → merged (merged = true, path = National Strategies' path)
(A+B) + C: 585 is not < 400                       → no
C + D: both < 400, but different parents          → no
result: [A+B 585] [C 307] [D 362]                 self-check: 585 + 307 + 362 = 1,254 = 290 + 295 + 307 + 362
```

The merged chunk takes the parent's path, since it holds two sub-sections. On Corpus D, merging at min 400 takes L4 from 209 chunks to 139 (70 merged), and the minimum stays 187: a small unit with no small sibling beside it cannot merge (S9).

**Key points** (a 3 needs every point):
- [ ] A and B merge (both < 400, same parent, 585 ≤ 1,000).
- [ ] C does not merge with A+B, because 585 is not below 400.
- [ ] C and D do not merge: different parents.

**For a 4, also:**
- [ ] Self-check: total length unchanged and every unit ≤ 1,000; says the merged chunk gets the parent's path and `merged = true`.

**Common wrong answers:**
- [ ] "A, B and C all merge: 892 ≤ 1,000": after A+B, the merged unit is no longer under min-chars.
- [ ] "C and D merge, both are small": they belong to different sections.

**If you missed it, reread:** [short §9](../reading/I2_structure_chunking.md#9-balanced-splitting-and-merging) · [short §7](../reading/I2_structure_chunking.md#7-the-section-tree-and-the-breadcrumb) · [lesson #s9](../lessons/I2_structure_chunking.html#s9) · book Ch14 p.4–5/13 (nearest page; per 04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-A-07 type=A set=main -->
### I2-A-07 · Application
**Question:** A teammate reads this table and says "L4 wins, ship it." What do you reply?

```
8 answerable llm-draft seeds, MiniLM-L6 (S14)
arm   chunks   mean length   CE@4   CE@budget (3,432 chars)   MRR@10
v0       97       857.9       8/8          8/8                0.708
L3      117       620.5       8/8          7/8                0.625
L4      209       347.3       7/8          8/8                0.917
seeds that straddle a v0 boundary: 0 of 8 · seeds whose evidence crosses a page: 0 of 8
```

**Reply template:** `Not yet: ____. The table cannot show ____. Next: ____.`

<details><summary>Hint 1</summary>

How many items, and who wrote them? Which column is the primary metric?

</details>

<details><summary>Hint 2</summary>

I2 fixes boundary failures. How many seeds test one?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Not yet. (1) Eight LLM-drafted seeds are observations, not an evaluation. (2) The primary metric is CE@4, and L4 is **worse** there (7/8: it misses D-007, a two-fact question that needs more small chunks); its MRR is high because small chunks put single facts at rank 1. (3) Chunk sizes differ (347.3 vs 857.9 characters), so fixed k compares different amounts of text; at the equal budget L4 recovers to 8/8, as v0 already is. (4) The bucket I2 targets is **empty**: 0 of 8 seeds straddle a boundary or a page. Verdict: **inconclusive**. Next: add `straddles_champion` and `crosses_page` items (M1), then compare with v0, the v1.0 champion and the cross-page control, at fixed k and equal budget, per bucket, and read the items that changed.

**Key points** (a 3 needs every point):
- [ ] 8 draft seeds are too few, and are observations, not results.
- [ ] The boundary bucket is empty (0 of 8), so the table cannot test what I2 fixes.
- [ ] Uneven chunk sizes: compare at equal budget too; L4 loses on CE@4 at fixed k (D-007).

**For a 4, also:**
- [ ] Names the next measurement: new bucket items, the cross-page control and champion as baselines, per bucket, reading 5 items that improved and 5 that got worse.

**Common wrong answers:**
- [ ] "0.917 is far above 0.708, so L4 is better": MRR on 8 draft seeds, and CE@4 at k = 4 is worse.
- [ ] "L3 is below v0, so structure-aware chunking does not work": the same 8 seeds cannot show that either.

**If you missed it, reread:** [short §13](../reading/I2_structure_chunking.md#13-measuring-it-inconclusive-on-8-seeds) · [lesson #s13](../lessons/I2_structure_chunking.html#s13) · book Ch9 p.10–11/14 (nearest page; per 02/04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-T-01 type=T set=main -->
### I2-T-01 · Transfer
**Question:** Corpus T has two-column papers with numbered, bold, body-size headings and a PDF outline. Which signal do you use first, and what do you check by eye?

**Reply template:** `First ____, because ____. Before that I fix ____. By eye I check ____. I would measure ____.`

<details><summary>Hint 1</summary>

Of outline, tags and typography, which gives titles and levels directly? What does it still not give?

</details>

<details><summary>Hint 2</summary>

What happens to sections and to alignment if two columns are read across the page?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** **The outline first** (`doc.get_toc()`): it gives titles, levels and pages directly. It does not give offsets, so each title is still aligned to the snapshot with the forward cursor, failing closed. Typography is the cross-check and the fallback: the headings are bold at body size, so a size-only rule would miss them; use size + bold, and the numbering gives the depth ("2.3" → level 2). **Before anything, fix the reading order** of the two columns (C1): read across the page, the sections interleave and alignment fails. By eye: one page's reading order, then the 10-chunk inspection sheet with a fixed seed (start, end, path, pages). Measure: heading counts per level against the outline, alignment of every title, then CE by bucket. Run `structure_fit_check.py` on T rather than trusting the rules tuned on D. When not to use it: if the outline is partial or the columns cannot be fixed, stay with the recursive chunker.

**Key points** (a 3 needs every point):
- [ ] The outline first, still aligned to exact offsets (it has no offsets of its own).
- [ ] Fix the two-column reading order before detecting or aligning anything.
- [ ] Typography as cross-check: size + bold (size-only misses body-size bold headings), numbering gives depth.
- [ ] By eye: one page's order and the fixed-seed 10-chunk sheet.

**For a 4, also:**
- [ ] A measurement (headings per level vs the outline, 100% alignment, then CE by bucket) and when not to use it (partial outline or unfixable columns → recursive chunker).

**Common wrong answers:**
- [ ] "Use the D rules as they are": they were tuned on one single-column PDF.
- [ ] "The outline is enough, no alignment needed": an outline gives titles and pages, not character offsets.

**If you missed it, reread:** [short §2](../reading/I2_structure_chunking.md#2-inside-the-pdf-blocks-lines-spans-and-the-bold-bit) · [short §5](../reading/I2_structure_chunking.md#5-error-modes-and-titles-that-repeat) · [short §14](../reading/I2_structure_chunking.md#14-when-not-to-use-it) · [lesson #s5](../lessons/I2_structure_chunking.html#s5) · [lesson #s12](../lessons/I2_structure_chunking.html#s12) · book Ch7 p.8/11 (nearest page; per 04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-T-02 type=T set=main -->
### I2-T-02 · Transfer
**Question:** v1.1 wins on the boundary bucket but loses on factual-single-span. Name two mechanisms that could cause this, and the trace you would read first.

**Reply template:** `Mechanism 1: ____. Mechanism 2: ____. I would first read ____ for the items that got worse.`

<details><summary>Hint 1</summary>

What changes about a chunk that holds a whole section, compared with a short focused one, when the question asks for one fact?

</details>

<details><summary>Hint 2</summary>

Besides the boundary rule, what else did v1.1 change, and what could the heading rules get wrong?

</details>

<details><summary>Show answer (write yours first)</summary>

**Model answer:** Candidate mechanisms (any two):
- **Granularity.** A section chunk mixes several facts, so a one-fact question matches it less sharply, and a smaller, focused chunk elsewhere outranks it. On the draft seeds, L4's small chunks put the single-fact seeds at rank 1, while L3's MRR was below v0's (0.625 vs 0.708).
- **Size and k.** L3 chunks are shorter (mean 620.5 vs 857.9), so 4 chunks carry less text; check at the equal budget before blaming the boundaries.
- **A second change.** Sections run across pages: compare with the cross-page control to see which change caused the loss.
- **Heading errors.** A missed or false heading, or a split point, separates a fact from its context.
- **Repeated sections.** Near-duplicate sections (the two "Paris Agreement" sub-sections) outrank the right one.

Trace first: for each item that got worse, the ranked list in both arms (chunk id, `[a, b)`, `section_path`, score) with the gold span marked: is the gold inside one chunk, and which chunk outranked it?

**Key points** (a 3 needs every point):
- [ ] One mechanism about granularity or chunk size (mixed-fact sections; less text at fixed k).
- [ ] A second, different mechanism (cross-page scope, heading errors, or duplicate sections).
- [ ] The trace: per item, both arms' ranked chunks with offsets, paths and scores, against the gold span.

**For a 4, also:**
- [ ] How to decide: fixed k and equal budget, per bucket with n, paired by item, against the cross-page control; adopt only if the bucket gain outweighs the loss on the larger category.

**Common wrong answers:**
- [ ] "Average all buckets; if the total is up, ship it": the loss may be on the bigger category.
- [ ] "It is noise, ignore it": read the items before deciding.

**If you missed it, reread:** [short §13](../reading/I2_structure_chunking.md#13-measuring-it-inconclusive-on-8-seeds) · [short §10](../reading/I2_structure_chunking.md#10-continuation-across-pages) · [lesson #s13](../lessons/I2_structure_chunking.html#s13) · book Ch9 p.10–11/14 (nearest page; per 02/04; not re-opened)

</details>
<!-- /q -->

<!-- q id=I2-T-03 type=T set=interview source=AIQ-04-Q4 -->
### I2-T-03 · Transfer (interview)
**Question:** "What chunking strategies do you know, and how do you pick one?" *From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, `04-rag-and-retrieval/questions.md` (Q4), Copyright (c) 2026 Om, MIT License.*

**Reply template:** `Strategies: ____. I pick by ____. Structure-aware helps when ____, and I check it by ____.`

<details><summary>Hint 1</summary>

List them from simplest to most elaborate, and name the one the course uses today.

</details>

<details><summary>Hint 2</summary>

Is any one strategy "best" in general? What decides it for your documents?

</details>

<details><summary>Show answer (write yours first)</summary>

The repository's answer (excerpt, verbatim, MIT License, Copyright (c) 2026 Om):

> From simplest to most sophisticated:
>
> - **Fixed-size**: cut every N tokens with overlap. Trivial to implement, ignores meaning - splits sentences and tables mid-thought. Acceptable baseline, rarely the end state.
> - **Recursive**: try splitting on big separators first (paragraphs), fall back to sentences, then tokens, until chunks fit the size limit. Respects natural boundaries; the sane default (LangChain's `RecursiveCharacterTextSplitter` popularized it).
> - **Structure-aware**: split along document structure - markdown headers, HTML sections, code functions - and attach the heading path ("Handbook > Benefits > Parental leave") to each chunk as context. Best choice whenever structure exists; the heading path alone fixes many retrieval misses.
> - **Semantic**: embed sentences, split where cosine similarity between adjacent sentences drops below a threshold. Conceptually appealing; in practice gains are marginal over recursive+structure-aware and it adds embedding cost at ingest.
> - **Late chunking**: embed the *entire* document with a long-context embedding model, then mean-pool token embeddings per chunk span afterward. Each chunk's vector is contextualized by the whole document - resolves pronouns and dangling references without an LLM call per chunk.
>
> Selection logic: use structure-aware when documents have structure (most do); recursive as fallback; consider contextual enrichment (prepending an LLM-generated situating sentence) or late chunking when chunks are ambiguous out of context. Also decouple the **retrieval unit from the generation unit**: retrieve precise small chunks but hand the LLM the surrounding parent section ("small-to-big" / parent-document retrieval) - small vectors match precisely, big context reads coherently.

**Model answer:** The family runs from fixed windows (every N characters or tokens, with overlap), through recursive splitting (the course's v0: 1,000 characters, overlap 200, per page), structure-aware splitting (this lesson), and semantic splitting, to "small-to-big" retrieval with parent sections. **Pick by measurement, not by rule**: on your own labelled questions, CE@k at fixed k and at equal budget, per bucket, against the strongest simple baseline, including a cross-page recursive control.

Two corrections to the repo's answer. First, "best choice whenever structure exists" is not what the studies found: they show **no consistent winner** (in one study plain recursive splitting beat structure-aware on editorial content; a vendor blog found page-level chunks best on average; both search-checked only, UNVERIFIED). On the climate PDF the result on 8 draft seeds is **inconclusive** (L3 MRR 0.625 vs v0 0.708; no seed tests a boundary). Second, "the heading path fixes misses" is a claim about putting the path **into the embedded text**: that is I5's experiment, not I2's. I2 keeps exact slices and stores the path as metadata. Structure must also be detected first: on the climate PDF 68.1% of headings are bold at body size, which a size-only converter misses.

**Key points** (a 3 needs every point):
- [ ] At least three strategies (fixed, recursive, structure-aware, semantic, parent/small-to-big).
- [ ] Choose by measuring on your own labelled questions (CE@k, fixed k and equal budget, per bucket).
- [ ] Corrects "best whenever structure exists": the evidence shows no consistent winner.
- [ ] Separates I2 from I5: the path as metadata vs embedding the path.

**For a 4, also:**
- [ ] A check and a limit: eye inspection and invariants before metrics, and when not to use it (no text layer, unreliable headings, no measured gain over the cross-page control).

**Common wrong answers:**
- [ ] "Structure-aware is always best when documents have headings": no consistent winner; measure it.
- [ ] "Attaching the heading path is part of structure-aware chunking, so it is free": embedding the path is a separate variable (I5).

**If you missed it, reread:** [short §13](../reading/I2_structure_chunking.md#13-measuring-it-inconclusive-on-8-seeds) · [short §14](../reading/I2_structure_chunking.md#14-when-not-to-use-it) · [short §7](../reading/I2_structure_chunking.md#7-the-section-tree-and-the-breadcrumb) · [lesson #s13](../lessons/I2_structure_chunking.html#s13) · book Ch9 p.10–11/14 (per 02/04; not re-opened)

</details>
<!-- /q -->
