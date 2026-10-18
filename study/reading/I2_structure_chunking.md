<!-- kit:reading concept=I2 depth=short version=1 -->
# I2: Structure-aware chunking

**What this is:** the short reading for I2, the text version of the HTML lesson's Short depth (`study/lessons/I2_structure_chunking.html`). It is enough to answer every question in `study/questions/I2_questions.md`.
**What this is not:** the lesson's Full sections (outlines and tags, frameworks, tables and layout models, the studies), or I5's experiment of embedding the heading path.

> **Read in the book:** Ch7 p.1–2/11 (chunks that lose their headings) before §1; Ch7 p.8/11 (chunk headers that carry a section path) before §7; Ch9 p.10–11/14 (where chunking strategies sit on a spectrum) before §8; Ch14 p.4–5/13 (working section by section) at the end. No chapter teaches I2 itself. These pages are listed per 04/07; **not re-opened in this session** (UNVERIFIED).

**Labels.** Numbers are **measured** on the climate PDF (Corpus D, 33 pages; PyMuPDF 1.26.7, snapshot `ea07572562ac`) unless marked **formula** or **toy**; the run section of [I2_FACTS](../../sources/verification/I2/I2_FACTS.md) is in brackets (S1–S14). The 8 seeds in §13 are LLM-drafted (`llm-draft`): observations, never evaluation results. No API was called.

**The answer first.** Structure-aware chunking cuts a document where its author cut it: at headings, with sections allowed to run across pages, instead of every N characters on each page. A PDF has no markup, so the structure is recovered from typography: larger or bold lines become headings, and their size rank becomes the level. The chunker builds a section tree, makes one chunk per section, splits long sections evenly, can merge tiny neighbours, and keeps every chunk an exact slice of the frozen text, so span gold and citations still work. On the climate PDF this repairs 16 orphaned headings and 8 page-cut sentences; but 192 of its 282 headings (68.1%) are bold lines at body size, which a size-only detector misses. Whether it retrieves better is an experiment, and on today's 8 draft seeds the honest verdict is **inconclusive**.

## 1. The failure: a heading at the bottom of a page

**The answer first:** v0 chunks each page on its own, so wherever a page ends, the chunk ends, even between a heading and its paragraph or in the middle of a sentence.

Refresher from C1: the snapshot is all page texts joined with `"\n"` (72,593 characters, S1). A chunk is a slice `[a, b)` of it; gold answer spans and citations are offsets into it.

v0 runs the recursive splitter (1,000 characters, overlap 200) inside each page: 97 chunks, none on two pages (S9). Page 1 ends like this (measured, S6):

```
... which continues to rise
today.
Coal                                  ← a sub-heading, the last line of page 1
--- page break ---
Coal is the most carbon-intensive fossil fuel, ...      ← its paragraph, on page 2
```

Counted over the whole PDF (S8):

```
pages that end in a detected heading (orphaned headings)      16
page breaks that cut a sentence in two                          8
page breaks not ending in . ! ? : or a quote               24 of 32
```

One cut sentence, pages 12→13: "Public-private partnerships (PPPs) can leverage resources, expertise, and innovation to implement | large-scale climate solutions." No v0 chunk holds the whole sentence, and no v0 chunk holds "Coal" together with its first body line (S12).

**What this means.** A heading alone at the end of a chunk is noise; the paragraph after it has lost its label; a cut sentence cannot be found whole. The book's chunking chapter describes this loss of headings (Ch7 p.1–2/11).

**For your project:** v1.1 cuts at headings, lets a section run across pages, and caps its length.

## 2. Inside the PDF: blocks, lines, spans and the bold bit

**The answer first:** PyMuPDF's `page.get_text("dict")` gives every piece of text with its size and style flags; headings are visible there, not in plain text.

The structure is page → blocks → lines → spans. A **span** is a run of text in one font, size, colour and style; a new span starts when any of them changes. Three real spans from page 1 (S2):

```
text                                          size   flags  char_flags  font
'Understanding Climate Change '               24.00   20     24        TimesNewRomanPS-BoldMT
'Chapter 1: Introduction to Climate Change '  18.00   20     24        TimesNewRomanPS-BoldMT
'Climate change refers to significant, ...'   12.00    4     16        TimesNewRomanPSMT
```

`flags` packs five yes/no facts into one number, one bit each: 1 superscript, 2 italic, 4 serif, 8 monospaced, **16 bold**. So 20 = 16 + 4 means bold serif, and 4 means serif only. The bold test (formula):

```
bold(span) = (flags & 16) != 0  or  (char_flags & 8) != 0
```

Bit 16 comes from the font's metadata; synthetic bold (drawn bold without that metadata) shows up in bit 8 of `char_flags`. `pymupdf4llm` checks both, and so does the course.

**Where structure can come from** (S1):

| Source | On Corpus D | How to use it |
|---|---|---|
| The outline (bookmarks), `doc.get_toc()` | `[]`: none | first choice when present: titles, levels, pages; each title must still be found in the text |
| PDF tags (`StructTreeRoot`) | present: a tagged Word 2021 PDF | a cross-check only |
| Typography: size and bold | four levels | the route this lesson builds |

## 3. The body size: count characters, not spans

**The answer first:** the body size is the font size that holds the most characters; every heading level is defined relative to it.

```
b = the size s with the largest total of len(text.strip()) over all spans of size s      (formula)
```

Corpus D, characters per size (S3):

| Size, style | Characters | Share |
|---|---|---|
| 24, bold | 28 | 0.0% |
| 18, bold | 855 | 1.2% |
| 13.56, bold | 1,666 | 2.4% |
| 12, bold | 4,057 | 5.8% |
| **12, regular** | **63,762** | **90.6%** |
| 11.04, regular (Calibri) | 0 (blank) | 0.0% |

So b = 12.0. Note the 12-point bold row: 4,057 characters of bold text **at body size**. Those are the sub-headings (§4).

**Why characters, not spans.** A span count measures how often the style changes, not how much text is set in a size. Blank spans count but hold no text (the 11.04-point Calibri spans hold 0 characters), and short labels, footnote marks or table cells make many tiny spans. On D the span count also points at 12 (1,006 spans at 12.0, 68 at 13.56); on a different file it may not.

## 4. Headings: size alone misses two-thirds of them

**The answer first:** a size-only rule misses every heading set bold at body size: 192 of 282 on D.

The rule, in three parts:
1. **Size rank.** The bold sizes above the body size, largest first, get levels 1, 2, 3 …
2. **Bold at body size.** A line that is all bold at the body size gets the next level.
3. **Filters** (project choices, [P]): at most 12 words; no final `.`, `!` or `?`; not on 3 or more pages (a running header or footer).

Numbered headings ("2.3 Methods") give a further signal: the depth of the number is the level.

Corpus D has 1,097 text lines, 283 all bold (S4). The two rules give:

```
rule            L1   L2   L3    L4    total
size only        1   21   68     –      90
size + bold      1   21   68   192     282
size only misses 192 of 282 headings (68.1%)
```

The levels on D: **L1** the title (24 pt), **L2** chapters (18 pt), **L3** sections (13.56 pt), **L4** sub-sections (12 pt bold), such as "Coal", "Oil" and "Paris Agreement".

**The tempting wrong idea:** "headings are the bigger text." `pymupdf4llm`'s header detection (0.2.9) is size-only, so on D it would miss all 192 (read from its source; not run here).

**For your project:** use "size rank, plus bold at body size"; keep size-only as a comparison arm (§8).

## 5. Error modes, and titles that repeat

**The answer first:** typography rules break in predictable ways, and the same title can appear in two places.

| Error mode | On Corpus D (S4) | The rule that handles it |
|---|---|---|
| A heading wraps onto two lines | Chapter 5's title wraps onto "Mitigation" (page 7): 22 level-2 lines → 21 headings | join consecutive heading lines of the same level in one block |
| A hyphen inside a heading | 15 such headings, e.g. "Public-Private Partnerships" (page 12) | none needed here: each is one span in PyMuPDF; check on other PDFs |
| A bold lead-in phrase inside a paragraph | none removed on D | the final `.` `!` `?` filter |
| Running headers, long bold lines | none on D | the "3 or more pages" and 12-word filters |
| Two columns, captions, tables | not on D | fix the reading order first (C1); the Full lesson |

**Repeated titles.** 11 titles appear twice, 22 headings in all (S7). "Paris Agreement" is a sub-heading on page 10 and on page 23, under different chapters. "International Agreements" is a sub-heading (L4) on page 6 but a section (L3) on page 23. **A leaf title is not an identity.** The full path is (§7).

## 6. Aligning every heading to the snapshot

**The answer first:** find each heading line in the snapshot text with a cursor that only moves forward, so every heading gets an exact offset; if one is not found, stop.

The `dict` output has fonts but no offsets; the snapshot has offsets but no fonts. They can be joined because both come from the same text page: the `dict` lines, each followed by `"\n"`, rebuild `page.get_text()` exactly on 33 of 33 pages (S5).

```
cursor = 0
for heading in reading order:
    pos = doc_text.find(heading_line, cursor)
    if pos == -1: raise an error                     ← fail closed
    heading.start, heading.end = pos, pos + len(heading_line)
    cursor = heading.end
```

Result (S6): **282 of 282 headings aligned**, each on its own page. "Coal" sits at `[2418, 2423)`; page 1's text ends at 2424, so it is the page's last line.

**Why a moving cursor.** A search from offset 0 returns the *first* match: the second "Paris Agreement" (page 23) would land on page 10, and a short title such as "Coal" also occurs in body text. **Why fail closed.** A skipped heading merges two sections, and nothing downstream would notice.

**Why not convert to Markdown first.** A common framework route is `pymupdf4llm` (PDF → Markdown), then LangChain's `MarkdownHeaderTextSplitter`. From the library source (not run here): the splitter strips every line and re-joins lines with `"  \n"`, so its output is **rewritten text with no offsets into the snapshot**; by default (`strip_headers=True`) the heading leaves the text and survives only as metadata; there is **no size cap**; and the converter's header detection is size-only (§4). Span gold cannot score such chunks until each is mapped back to the snapshot; the course chunker keeps exact slices instead.

## 7. The section tree and the breadcrumb

**The answer first:** each heading owns the text up to the next heading of the same or a higher level; the titles of the headings still open above it form its path.

```
section(h) = [start(h), start(next heading with level <= level(h)))                (formula)
path(h)    = keep a stack; pop while the top's level >= level(h); push h; read the titles
```

Chapter 6 (S7), lengths in characters from the heading to the end of its section:

```
L2 Chapter 6: Global and Local Climate Action           2728  page 10
  L3 International Collaboration                          695
    L4 United Nations Framework Convention ... (UNFCCC)   348
    L4 Paris Agreement                                    318
  L3 National Strategies                                  913
    L4 Carbon Pricing 290 · Renewable Energy Targets 295 · Emission Reduction Regulations 307
  L3 Local and Community Initiatives                     1076
    L4 Urban Climate Action 362 · Community-Based Conservation 346 · Education and Awareness 335 (page 11)
```

The two "Paris Agreement" headings, told apart by their paths:

```
page 10  Chapter 6: Global and Local Climate Action > International Collaboration > Paris Agreement
page 23  Chapter 16: Global Cooperation and Governance > International Agreements > Paris Agreement
```

The document title (L1) sits above every path and is left off.

**Where the path lives.** A chunk is an exact slice of the snapshot. Its own heading sits at the start of its section, inside the slice. Its parents' headings sit earlier in the document, outside it, so adding them to the chunk text would break the offsets. The path goes into metadata (`section_path`) instead. The book suggests richer chunk headers with such a path (Ch7 p.8/11). Putting the path into the text that gets embedded is I5's experiment, kept separate so that v1.1 changes one thing.

## 8. Choosing the split level

**The answer first:** the split level decides which headings start a new chunk; on D the section level (L3) fits a 1,000-character cap best, and it is the main path.

At split level L, every heading at levels 1 to L starts a new unit; deeper headings stay inside. **A heading never ends a unit:** a chapter heading followed directly by its first section heading glues forward into the same chunk. Long units are then split (§9). Cap C = 1,000 characters ([P]); no overlap inside a section.

Chunk arms on D (S9):

| Arm | Chunks | Length min / median / max | Mean | On two pages |
|---|---|---|---|---|
| v0, per page 1000/200 | 97 | 393 / 935 / 1000 | 857.9 | 0 |
| Cross-page recursive 1000/200 (control) | 92 | 755 / 962.5 / 999 | 954.8 | 41 |
| Structure, split at L2 | 86 | 644 / 843.5 / 1000 | 844.1 | 29 |
| **Structure, split at L3** | **117** | **187 / 619 / 997** | **620.5** | **27** |
| Structure, split at L4 | 209 | 187 / 338 / 636 | 347.3 | 24 |
| Structure, L4 + merge (min 400) | 139 | 187 / 545 / 772 | 522.3 | 25 |

Why L3: the median section length (S7) is 3,336 characters for L2 chapters, 1,033.5 for L3 sections and 334 for L4 sub-sections. L3 is close to the cap; chapters need several pieces; sub-sections are small. A simple rule: **the deepest level whose median section is at least the minimum size** (400 [P]): L4's 334 is below 400, L3's 1,033.5 is above, so L3. At L3, 46 of the 71 units are over the cap.

**A surprise worth remembering:** at L3, the size-only detector gives **exactly the same 117 chunks** (S9). The 192 bold sub-headings change nothing at section level. They matter when you split at L4, and for the breadcrumb.

## 9. Balanced splitting and merging

**The answer first:** a long section is cut into n near-equal pieces at sentence ends, not full pieces plus a tiny tail; tiny neighbours can merge up to the cap.

```
n = ⌈ℓ / C⌉ pieces, ideal length ℓ / n                                                (formula)
each cut: the sentence-ending line break within half a piece of its ideal point,
          else the nearest line break; never inside or right after a heading
```

Measured cases (S10):

```
Ch11 > Advocacy and Activism   ℓ = 1,004   n = ⌈1004/1000⌉ = 2   ideal 502 each
    balanced: 341 + 663          (the sentence end nearest 502)
    naive cap cutting: 1,000 + 4  ← a 4-character chunk
Ch2 > Greenhouse Gases         ℓ = 1,935   balanced: 990 + 945
```

**Merging** answers the opposite problem: at L4, many chunks would be tiny. The merge rule (S9):

```
while two adjacent units are both < min_chars, have the same parent path, and together <= C:
    merge them; merged = true; path = the parent's path
```

With min 400, L4 goes from 209 chunks to 139, and 70 of them are merged chunks. On Chapter 6, Carbon Pricing (290) and Renewable Energy Targets (295) meet every condition: both under 400, same parent, together 585 ≤ 1,000 (formula on the S7 lengths). The minimum stays 187: a small unit with no small sibling beside it cannot merge.

## 10. Continuation across pages

**The answer first:** a structure chunk may run across a page break; it keeps one exact range, plus a list of page pieces for citations.

The two failures of §1, re-checked (S12):

```
"Coal" + its first body line in one chunk     v0: no     L3: yes (chunk 3, pages 1–2)
whole PPP sentence (pages 12→13) in one chunk    v0: no     L3: yes, path Chapter 8 > Policy and Governance
                                              L2, L4, L4 + merge: yes     cross-page control: yes
```

At L3, 27 of the 117 chunks lie on two pages. Each chunk stores `page_segments`: a list of `(page, a, b)` pieces that together rebuild `[a, b)`. A chunk on pages 1–2 can therefore cite both pages exactly.

**Caveat, stated plainly:** the cross-page control keeps the PPP sentence whole too: page scope alone repairs cut sentences. Against per-page v0 alone, v1.1 changes two things (boundary rule and page scope); the control separates them.

## 11. The invariants that protect span gold

**The answer first:** five properties must hold for every chunk, or the offsets that span gold and citations rely on are wrong.

```
assert doc_text[c.a:c.b] == c.text                      # round trip: an exact slice
assert c.b - c.a <= C                                   # the cap
assert not doc_text[prev.b:c.a].strip()                 # no gaps: only whitespace between chunks
assert no split-level heading starts strictly inside [c.a, c.b),
       unless only headings come before it in the chunk (a glued heading run) or c.merged
assert pieces of c.page_segments rebuild [c.a, c.b)     # citations
```

Result (S11): **0 violations in every structure arm.** The L3 chunks tile the document with no overlap.

## 12. Eye inspection before any metric

**The answer first:** read 10 random chunks, chosen with a fixed seed, against a short sheet before you trust any score.

The sheet: starts at a heading or a clean continuation; ends at a sentence end; right path; no heading stranded at the end; right pages. `random.Random(0).sample` of the L3 chunks gives chunks 5, 33, 49, 51, 53, 62, 65, 97, 108 and 113 (S13). **10 of 10 start at a heading and end at a sentence end.** Chunks 65 and 108 are second pieces of a split section, so they start at a sub-heading. Chunks 51 (pages 15–16), 62 (pages 18–19), 97 (pages 27–28) and 108 (pages 30–31) run across a page break. Paths: correct by eye (the tutor's reading); your own verdict sheet is the notebook's task.

**Why first:** a wrong heading rule shows up in a metric as a retrieval miss, blamed on the retriever. Rule of thumb ([P]): fewer than 8 of 10 pass → fix the parsing before measuring.

## 13. Measuring it: inconclusive on 8 seeds

**The answer first:** on the 8 draft seeds no arm clearly wins, and none of the seeds tests the failure I2 fixes, so the verdict is **inconclusive**.

The setup (S14): MiniLM-L6 (its ONNX export in this session), exact cosine. CE@4 asks whether the whole evidence is inside the top 4 chunks. Chunk sizes differ (L3 mean 620.5, v0 857.9), so each arm is also measured at an **equal budget**: 4 × v0's mean chunk length = 3,432 characters (formula), filled in rank order.

| Arm | Chunks | CE@4 | CE@budget | MRR@10 (first hit) |
|---|---|---|---|---|
| v0 | 97 | 8/8 | 8/8 | 0.708 |
| Cross-page control | 92 | 7/8 | 6/8 | 0.604 |
| L2 | 86 | 8/8 | 8/8 | 0.792 |
| **L3** | **117** | **8/8** | **7/8** | **0.625** |
| L4 | 209 | 7/8 | 8/8 | 0.917 |
| L4 + merge | 139 | 7/8 | 8/8 | 0.771 |

**What this means.** L4's small, focused chunks put the single-fact seeds at rank 1, but miss D-007 at k = 4: a two-fact question needs more small chunks. At the equal budget L4 recovers. L3 is no better than v0 here. And the bucket that matters is empty: **0 of 8 seeds straddle a v0 boundary, 0 of 8 cross a page.** No chunk in any arm is over MiniLM's 256 tokens. Published comparisons disagree too: **no consistent winner** among structure-aware, recursive and page-level chunking (Full lesson; search-checked, UNVERIFIED).

**For your project:** before v1.1 is measured, M1 must add questions whose evidence straddles the champion's chunk boundaries (`straddles_champion`) or a page (`crosses_page`). Then compare v1.1 with v0, the v1.0 champion and the cross-page control, at fixed k and equal budget, per bucket, and read 5 items that got better and 5 that got worse.

## 14. When not to use it

- **No text layer** (scans): no typography to read. Use the recursive v1.0 chunker, or OCR and layout models first.
- **Unreliable headings:** fewer than 8 of 10 inspected chunks pass.
- **Two columns not handled:** fix the reading order first (C1), or sections interleave.
- **Rules tuned on D, used elsewhere:** run `study/tools/structure_fit_check.py` on Corpus T first.
- **No measured gain:** if v1.1 does not beat the cross-page control on the boundary bucket, keep the simpler chunker. "Inconclusive" is not a win.
- **Tables:** keep them whole (C7, S2); D has none.

## Check yourself

→ `study/questions/I2_questions.md`. Verify every number yourself: `study/notebooks/I2_structure_chunking_verify.ipynb`. Use the checks on your own PDFs: `study/tools/structure_fit_check.py`.
