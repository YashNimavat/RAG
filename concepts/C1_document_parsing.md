# C1 — Document loading and parsing: pages, the frozen text snapshot, and extraction artifacts

> **What this file is.** The lesson for concept **C1** ([02 card](../02_RAG_MASTER_LEARNING_PLAN.md#c1)), the first lesson of Phase 2 (building **v0**). It follows the Parts A–M template of [07](../07_SAMPLE_LESSON.md), at the size of [P4](P4_embeddings_similarity.md).
> **How to use it.** Answers are hidden in collapsible blocks. Write your answer first, then open the block. Lines marked `> 🧭 Coach:` are instructions for the AI tutor; they add to [05 §3](../05_LEARNING_AND_RETENTION_SYSTEM.md#3-coaching-rules-for-the-ai-tutor) and cannot override it.
> **Labels.**
> - **UNVERIFIED**: not checked by running code or reading the primary source.
> - **Toy illustration**: numbers computed by code on made-up data (the synthetic "artifact zoo" PDF, or tiny hand examples), never a result about a real corpus.
> - **Specimen**: a real page of the book PDF used only to show an artifact. The book is **not** a corpus ([06 §5.1](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#51-the-three-corpora)).
>
> Every number here comes from the local runs of 2026-10-08 ([C1_FACTS.md](../sources/verification/C1/C1_FACTS.md), sections S1–S12), from a logged earlier run (cited), or carries a label. No Groq or Cohere call was made.

## Lesson header

| Field | Value |
|---|---|
| Concept | **C1 Document loading and parsing**: PyMuPDF page-level extraction that keeps `doc_id` and 1-based `page`; the frozen text snapshot and its `snapshot_id` (which depends on the parser version, pinned at 1.26.7); extraction artifacts (hyphenation, ligatures, headers/footers, two-column order, tables, empty and image-only pages, figures); deciding cleaning rules and logging what they remove; why v0 does **no** cleaning. |
| Phase / tier | Phase 2, Core RAG baseline → v0. Priority **E**. No fast track ([02](../02_RAG_MASTER_LEARNING_PLAN.md#c1)). |
| Prerequisites | **O2** (environment, pinned `pymupdf==1.26.7`), **P2** (documents and queries). Useful: **P1** (characters vs tokens). |
| Comes next | **C2** chunking ([07](../07_SAMPLE_LESSON.md)), which reads this lesson's pages and snapshot · **C3** embedding and indexing (stores the `snapshot_id`) · **M1** span-level gold labels (they point into this snapshot) · **I2** structure-aware chunking. |
| Time | A: 10 min · book block: 15 min · B–D: 50 min · E–G: 20 min · H (lab): 60–75 min · J–K: 15 min · L: 15 min · M: 5 min. May be split across two days. Part I does not apply. |
| Mastery (C1 → `applied`) | Without notes, you can: (1) load a PDF into `Page(doc_id, page, text, parser)` records with 1-based pages; (2) build `doc_text` and the page table and map an offset back to a page; (3) compute the `snapshot_id` and say what changes it; (4) name five extraction artifacts and how to detect each; (5) explain why v0 does no cleaning. Lab: `coding_independence_0_3 ≥ 2`. |
| Mastery (C1 → `transfer`) | You also pass a fresh novel-scenario item (L.3) and score `debugging_0_3 ≥ 2` in the lab. |
| 02 evidence to produce | An artifact log with before/after snippets and page provenance for every character. For **Corpus D and the zoo**: lab Tasks 6–8. For **Corpus T**: **pending**, because the T file list is not chosen yet (D-01/D-02 decide its make-up; the concrete list is proposed at C1; see Part H.4). |

### Source map

| Source | Where | What it contributes |
|---|---|---|
| Book (A) | Ch1 p.4/14, p.5/14, p.7/14; Ch2 p.4/11; Ch3 p.1/14; Ch14 p.5/13; Ch16 p.1/11, p.4/11, p.10/11 | "Poor extraction leads to poor retrieval"; a one-line cleaning step; visuals are invisible to text extraction; page metadata. **No** artifact catalogue, no library, no offsets, no snapshot. |
| Specimens (book PDF) | Ch1 p.2/14 (a figure), p.13/14 (a table); `intro.pdf`, `index.pdf` (repeated lines) | Real artifacts measured in S8 |
| Repo (B) | `helper_functions.py:L18-L31`, `L48-L76`, `L223-L245`; `simple_rag.ipynb` cell 10; `multi_model_rag_with_captioning.ipynb` cells 8–9 | Two different PDF readers; tab-only cleaning, applied **after** splitting |
| Our records | [06 §2.3, §3.1, §5.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#53-corpus-freezing) (data model, v0 spec, snapshot recipe); [LAB_FACTS §7](../sources/verification/LAB_FACTS.md) (PyPDFLoader on Corpus D) | The interface this lesson implements |
| Lab verification | [`sources/verification/C1/`](../sources/verification/C1/): `c1_measure.py`, `c1_sources.py`, `c1_crossversion.py`, the zoo builder, saved outputs, [`C1_FACTS.md`](../sources/verification/C1/C1_FACTS.md) | Every measured number here |

### Contents

[Part A](#part-a--prior-knowledge-recovery) · [Read in the book](#read-in-the-book) · [B](#part-b--why-c1-exists) · [C](#part-c--intuition-and-analogy) · [D](#part-d--technical-mechanism) · [E](#part-e--connections) · [F](#part-f--worked-example-by-hand) · [G](#part-g--source-connection) · [H](#part-h--implementation-progression) · [I](#part-i--controlled-experiment) · [J](#part-j--failure-and-debugging) · [K](#part-k--engineering-decisions) · [L](#part-l--assessment) · [M](#part-m--retention) · [References](#source-references) · [Verification log](#verification-log)

---

## Part A — Prior knowledge recovery

Answer the five questions **before** reading on: 1–3 sentences each, no notes. Wrong answers are useful.

> 🧭 Coach: Ask **one item at a time** (CR-01), in the exact wording below, with its reply template. Record confidence 1–3 before revealing anything (CR-16). Score with the Recall rubric ([05 §4.2](../05_LEARNING_AND_RETENTION_SYSTEM.md#42-graded-rubrics-04)). These are unscheduled recall items: log them, do not change the schedule, except that a score ≤ 1 follows the ≤ 1 row of [05 §5.2](../05_LEARNING_AND_RETENTION_SYSTEM.md#52-spaced-repetition-schedule). Do not teach yet; route with the table after C1-A5. The learner is often confident and wrong (O1): say so if it happens.

**C1-A1.** A PDF goes into a parser. What comes out for each page?

*Reply template:* "For each page I get ____. I should also keep ____ next to it."

<details><summary>What a strong answer contains</summary>

- The page's **text** as a string, in the order the parser reads it.
- Kept next to it: the **document id** and the **page number** (1-based PDF page), plus which parser and version made it. In v0 that is `Page(doc_id, page, text, parser)` ([06 §3.1](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#31-stage-by-stage-specification)).

</details>

**C1-A2.** Why must every chunk remember its page number?

*Reply template:* "Because the answer must ____, and without the page we cannot ____."

<details><summary>What a strong answer contains</summary>

- Citations: v0 answers cite `[doc_id:page]` ([06 §3.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#33-v0-prompt-template-promptsanswer_v1txt)), so a human can open the page and check.
- Evaluation: gold evidence is stored as character spans on pages (M1). Lose the page and you can neither cite nor score.
- ⚠️ Flag: "the page number is in the text anyway". It is not: no line of Corpus D repeats across pages even with digits masked, so there are no page-number lines (S5).

</details>

**C1-A3.** Name two things that can go wrong when text is pulled out of a PDF.

*Reply template:* "One problem is ____. Another is ____."

<details><summary>What a strong answer contains</summary>

Any two of: words split by line-end hyphens; ligature characters (`ﬁ` instead of `fi`); headers and footers repeated on every page; two columns read across instead of down; tables flattened into one cell per line; figures (their text is pixels, so it is lost); empty or scanned pages that give no text; sentences cut at page breaks. All measured in D.4.

</details>

**C1-A4.** Should we clean the extracted text before we save it? Why or why not?

*Reply template:* "I would ____, because ____."

<details><summary>What a strong answer contains</summary>

- For v0: **no**. Offsets, page tables and gold labels must refer to the **raw** text, and a cleaning step is a decision that needs evidence ([06 §2.4](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#24-configuration-yaml-example) `cleaning: none`).
- Any cleaning is a recorded step that creates a **new snapshot**. Analysis rules can still be run and **logged** without changing the text (D.5).
- ⚠️ Flag: "always clean, it can only help". On Corpus D a naive de-hyphenation rule would damage 7 of 7 words it touches (S5).

</details>

**C1-A5.** Two Python libraries read the same PDF. Will they give exactly the same text?

*Reply template:* "____, because ____. This matters because ____."

<details><summary>What a strong answer contains</summary>

- **No, not exactly.** On Corpus D, pypdf and PyMuPDF give the same words on 33 of 33 pages but byte-identical text on 0 of 33 (PyMuPDF adds a final `"\n"` to every page) (S11).
- So character offsets and hashes differ, and chunks built from one cannot be matched against labels made on the other. That is why the parser and its version are part of the `snapshot_id`.

</details>

> 🧭 Coach: **Routing.**
>
> | Weak answers (score ≤ 1) | Action |
> |---|---|
> | C1-A1 or C1-A2 | Teach D.1–D.2 slowly; do Part F on paper before any code. |
> | C1-A3 | Teach D.4 with the zoo outputs first; read Ch16 p.1/11 together. |
> | C1-A4 | Teach D.5 and K; ask the CR-08 probe in Part F. |
> | C1-A5 | Teach D.3 and D.6 together. |
> | All five ≥ 3 with confidence 3 | Go faster through B–D, but do every lab task (no fast track for C1). |

---

## Read in the book

> 📖 **Read these pages now (after Part A, never before), in this order.** Each takes 2–4 minutes. After each page, close the book and write one line from memory.
>
> | When | Pages | Look for |
> |---|---|---|
> | Now | **Ch1 p.4/14** (Step 1: Load) | The page-by-page parse; the claim that weak extraction weakens retrieval; the librarian copying a book onto index cards. |
> | Now | **Ch1 p.5/14** (Step 3: Clean), then **Ch1 p.7/14** (the sketch) | Which artifacts the book names (tabs, extra spaces, broken line endings). Notice the **order**: the book splits first (Step 2) and cleans each chunk afterwards. We will do the opposite (D.5). |
> | Now | **Ch16 p.1/11** and **p.4/11** | Why figures and image tables are invisible to text extraction; images tagged with their page. |
> | After D.4 | **Ch3 p.1/14** | A retrieved chunk that is only a page footer full of links. That is the symptom of header/footer noise. |
> | After D.4 | **Ch16 p.10/11**, **Ch2 p.4/11** | When captioning is overkill (the parser already gives tables as text); a PDF gives one continuous stream, a CSV gives rows. |
>
> **What the book does not cover** (checked by text search over every chapter, S-src): hyphenation, ligatures, two-column reading order, scanned pages or OCR, any named PDF library, page numbering conventions, character offsets, and freezing the extracted text. This lesson fills those gaps.
>
> 🧭 Coach: one question after the reading only: "In the book, does cleaning happen before or after splitting into chunks?" Expected: after; Step 2 split, Step 3 clean (Ch1 p.4–5/14), and the sketch says "clean each chunk" (Ch1 p.7/14).

---

## Part B — Why C1 exists

### B.1 Three silent problems, none of which raises an exception

1. **Lost pages.** The repo's `read_pdf_to_string` (`helper_functions.py:L223-L245`) glues pages with no separator and returns one string. Page 33 starts at offset 71,925 there but at 71,957 in our `doc_text` (S4). No page numbers survive, so no citation is possible.
2. **A different extractor, different offsets.** pypdf and PyMuPDF give the same words but never the same bytes on Corpus D (S11). A gold span labelled on one is off by one character per page on the other.
3. **Text that is not there.** The figure on book Ch1 p.2/14 is an image: zero text blocks overlap it (S8). The zoo's "scanned" page returns an empty string, exactly like a blank page (S9).

### B.2 What C1 adds

The book gives C1 one paragraph (Ch1 p.4/14) and one cleaning step (Ch1 p.5/14). We add: page records with provenance, one coordinate system, a frozen snapshot with a recomputable id, a measured artifact inventory, and a cleaning log that keeps every character traceable.

---

## Part C — Intuition and analogy

**A photocopy with a page index.** The book's analogy is a librarian copying a book onto index cards (Ch1 p.4/14). Add two rules:

- **Number every card with its book and page.** That is `Page(doc_id, page, text, parser)`.
- **Never correct the copy in place.** If you fix a typo on a card, every bookmark pointing at "card 6, character 1,874" now points at the wrong letter. You may write corrections on a separate sheet (the cleaning log), each one saying what was at which position.

**Where the analogy breaks.** A librarian reads the page as a human. A parser reads the PDF's drawing instructions, in the order they were written. That order is not always the reading order: the zoo's two columns come out line by line across the page (S9).

> 🧭 Coach: CR-17. Stop and ask one question: "You fix one typo on page 2 of the copy. What happens to a bookmark that points at character 100 of page 5 in the joined text?" Expected: it shifts by however many characters the fix added or removed, so it points at the wrong text.

---

## Part D — Technical mechanism

> 🧭 Coach: CR-17. Teach one chunk per turn. Each subsection ends with its question below; the longer ones also have `⏸` checkpoints, each with one question. D.1: "Is the first page 0 or 1 in our records?" · D.2: "Which page owns the joining newline after page 1?" · D.3: "Same text, newer pymupdf: same snapshot_id?" · D.4: "Which artifact makes a blank page and a scanned page look the same?" · D.5: "Why does R2 delete only the hyphen and the newline?" · D.6: "Which repo reader loses page numbers?"

### D.1 What a PDF parser gives you

- A PDF page is a list of drawing instructions ("put these glyphs at x, y"). `page.get_text()` turns the text instructions back into a string, in the order PyMuPDF groups them. It returns layout newlines, not paragraphs.
- On Corpus D: 33 pages, 636 (p.33) to 2,494 (p.19) characters each, 72,561 in total (S2). Every page ends with `"\n"`; 1,093 of its 1,100 lines end with a space before the newline (S5).
- `get_text()` and `get_text("text")` are the same call (identical on 33/33 pages, S4). `get_text(sort=True)` is a different option: it changed the whitespace on all 33 pages (same words) (S4).
- v0 stores each page as `Page(doc_id="climate", page=1..33, text=<raw get_text()>, parser="pymupdf 1.26.7")` ([06 §3.1](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#31-stage-by-stage-specification)). PyMuPDF counts pages from 0; **our** `page` is 1-based, matching how humans and citations count.

### D.2 One coordinate system: `doc_text` and the page table

```text
doc_text = "\n".join(page texts)          # 72,561 + 32 joins = 72,593 characters (S2)
row(p)   = {page, doc_char_start, doc_char_end, text_sha256}
           doc_text[doc_char_start:doc_char_end] == page text      (true for all 33 pages)
next start = previous end + 1             # the joining "\n"
```

- Real rows (S2): page 1 = [0, 2,424); page 2 = [2,425, 4,835); page 8 starts at 16,074; page 33 = [71,957, 72,593).
- **Who owns the join?** Offset 2,424 (the `"\n"` after page 1) maps to page 1, offset 2,425 to page 2 (S6), the same rule as 07's `page_of`.
- **Lookup.** The first "Paris Agreement" is at offset 13,420, which is page 6, page offset 1,874. It occurs 8 times, on pages 6, 10, 23 and 24 (S6), as 06 §5.1 lists.
> ⏸ Checkpoint (one question): "Page 2 is 2,410 characters long. Where does page 3 start?" Expected: 4,835 + 1 = 4,836 (S2 row 3).

- **A trap for C2:** inside pages there is no `"\n\n"` at all, but `doc_text` has exactly 32, one at each page join (S2, S5). C2's splitter tries `"\n\n"` first, so it fires only at page breaks.

### D.3 The frozen snapshot and its `snapshot_id`

The PDF lock freezes **bytes**. The snapshot freezes the **extracted text** that chunks and gold labels point into ([06 §5.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#53-corpus-freezing)). Its id is the recipe in 06 §5.3:

```python
parts = ["snapshot-v1", f"parser={backend}@{version}", "options=" + json.dumps(options, sort_keys=True),
         f"cleaning={cleaning_version}", "page_join=\\n"]   # literal backslash + "n"
parts += [f"{doc_id}:{doc_text_sha256[doc_id]}" for doc_id in sorted(doc_text_sha256)]
snapshot_id = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
```

For Corpus D with PyMuPDF 1.26.7, options `{}`, cleaning `none`: **`ea07572562ac`** (S2), the same value as 06, the acceptance suite and the C2 lab's setup.

> ⏸ Checkpoint (one question): "Which five things feed this hash?" Expected: backend@version, options, cleaning version, the page join, and each document's text hash.

| Change one input (S3) | `snapshot_id` |
|---|---|
| none (v0) | `ea07572562ac` |
| version `1.28.2`, text byte-identical | `4b7e61b9e418` |
| cleaning `tabs_v1` (Corpus D has 0 tabs, so the text is unchanged) | `6164dfc95324` |
| options `{"sort": true}` (text not recomputed) | `f1e46e7c3c68` |
| one extra space at the end of page 1 | `a79df757e413` |
| `page_join=\n` written as a real newline (a bug) | `5ad6acfd28ec` |

> ⏸ Checkpoint (one question): "Corpus D has no tabs. Does a tab-replacing cleaning step change the id?" Expected: yes (`6164dfc95324`), because the cleaning version is in the recipe.

- **Why the version is in the id even when the text is identical.** PyMuPDF 1.28.2 gave byte-identical text on Corpus D (same `doc_text_sha256`, S11). On another PDF it may not, and you would not know without re-checking. The id makes "I re-checked" an explicit, recorded event.
- **Why pin.** The project pins `pymupdf==1.26.7` so the same machine always rebuilds `ea07572562ac`.
- **Writing it on Windows.** A plain `open(path, "w")` turns each of the 1,132 newlines into `"\r\n"`: 73,727 bytes on disk instead of 72,595, and the file hash no longer matches (S7). Reading back in text mode hides this. Write with `newline="\n"`.

### D.4 Artifact catalogue (measured)

| Artifact | What you see in `get_text()` | Where measured | v0 action |
|---|---|---|---|
| Line-end hyphen | `cost-\ncompetitive` | Corpus D: **7**, all real compound words; the joined form never occurs elsewhere, the hyphenated form always does (S5) | Keep. Log only |
| Ligature glyphs | `ﬁ` (one character, U+FB01); a search for "file" fails | Zoo: 3. Corpus D: 0 (S5, S9). PyMuPDF keeps ligatures by default | Keep |
| Header / footer | the same line on many pages; in the zoo the footer comes out **second**, not last | Zoo: 2 lines × 3 pages. `intro.pdf`: a website footer on 4 of 8 pages. Corpus D: none (S5, S8, S9) | Keep |

> ⏸ Checkpoint (one question): "Would de-hyphenating Corpus D help?" Expected: no; all 7 are real compounds such as well-being (S5).

| Artifact (continued) | What you see in `get_text()` | Where measured | v0 action |
|---|---|---|---|
| Two columns | lines alternate left, right, left, right | Zoo p.1: order L1 R1 L2 R2 …; `sort=True` puts both columns on one line; clipping each half fixes it (S9) | Not present in D (one x0 = 72) |
| Table | one cell per line; rows lost | Book Ch1 p.13/14: `find_tables()` finds 0; the text strategy finds a 45 × 9 grid of word fragments (S8). Zoo: ruled table found correctly (S9) | Keep |
| Figure / image | nothing; only the caption, if it is text | Ch1 p.2/14: 0 text blocks inside the image (S8) | Out of scope (S2 multimodal) |
| Empty vs image-only page | `""` for both | Zoo p.3 (0 images) and p.4 (1 image) (S9) | Flag image-only pages |
| Page-break cut | sentence split over two pages | Corpus D: 24 of 32 breaks end without final punctuation; 8 are mid-sentence (S5; same 8 as LAB_FACTS §7 with PyPDFLoader) | C2/I1 problem |

> ⏸ Checkpoint (one question): "A page gives an empty string. How do you tell a blank page from a scanned one?" Expected: count its images; the zoo's blank page has 0, the scanned page 1 (S9).

**Two artifacts can compound.** PyMuPDF's own `TEXT_DEHYPHENATE` flag on the zoo's interleaved columns produced "extracreading": the end of a left-column line glued to the next right-column line. With column clipping first, the same flag gives the correct "extraction" (S9).

> 📖 Now read **Ch3 p.1/14**, then **Ch16 p.10/11** and **Ch2 p.4/11**.

### D.5 Cleaning rules that log every change

A cleaning rule is a list of **edits**: `{doc_id, page, rule, start, end, before, after}` on raw page offsets. Applying edits gives the cleaned text plus a map `src[i]` = raw offset of cleaned character `i`. Undoing them gives back the raw text exactly. So every character keeps its page and position.

| Rule (analysis only) | Zoo (S10) | Corpus D (S10) |
|---|---|---|
| **R1** drop a line repeated on ≥ max(3, half the text pages), digits masked | 6 lines | 0 |
| **R2** delete `-\n` only if the joined word occurs elsewhere in the document | 1 ("extrac-\ntion") | 0 (a naive rule: 7, all wrong) |
| **R3** ligature → NFKC letters | 3 | 0 |

> ⏸ Checkpoint (one question): "Why does R2 check that the joined word occurs elsewhere?" Expected: to avoid gluing real compounds; on Corpus D the joined forms never occur, the hyphenated forms always do (S5).

- Zoo totals: 92 raw characters removed, 6 inserted; `undo(apply(edits)) == raw` on every page (S10).
- R2 deletes only the 2 characters `-\n`, so the letters of "extraction" keep their exact raw offsets (101–112 on zoo page 1, S10).
- **Rules can be wrong.** R1 on the book's `index.pdf` flags 5 real section titles ("#. The Problem" on 6 of 6 pages) (S8). A rule needs a log and a look.

> ⏸ Checkpoint (one question): "R1 flags '#. The Problem' on every page of `index.pdf`. Is that a footer?" Expected: no, it is a real section title, so R1 has false positives (S8).

**Why v0 applies none.** 06 fixes `cleaning: none`: chunk offsets and M1's gold spans refer to the raw snapshot. On Corpus D the three rules change nothing, and the obvious extra rule (naive de-hyphenation) would only do harm. The book cleans **after** splitting (Ch1 p.5/14, p.7/14), and so does the repo (`helper_functions.py:L69-L70`); either way the chunk text no longer equals a slice of any stored text. If a later version adopts a rule, it runs **before** chunking, gets a cleaning version, and creates a new snapshot.

### D.6 The repo has two PDF readers

| Reader | Used by | Pages kept? | Text on Corpus D |
|---|---|---|---|
| `PyPDFLoader` (pypdf), in `encode_pdf` `L62-L63` | 23 code locations (S-src) | Yes, one Document per page; metadata `page` is **0-based** (LAB_FACTS §7) | Same words; each page lacks PyMuPDF's final `"\n"`; joined 72,560 characters with pypdf 6.19.0 (S11) |
| `read_pdf_to_string` (PyMuPDF), `L223-L245` | 8 code locations | **No**: `content += page.get_text()` | 72,561 characters, no separators (S4) |
| `multi_model_rag_with_captioning.ipynb` cell 9 (PyMuPDF) | 1 notebook | Yes, `page_number+1` (1-based) | `.strip()` per page: 70 characters fewer on Corpus D (S4) |

The 07 lab measured 72,523 characters through `PyPDFLoader` (LAB_FACTS §7). Raw pypdf gives 72,560; the 37-character gap is LangChain post-processing that was **not** investigated (UNVERIFIED).

---

## Part E — Connections

**O2** (pinned environment) and **P2** (documents) → **C1** → **C2** chunking (reads `pages` and `doc_text`) → **C3** embedding (stores `snapshot_id` in the index manifest) → **M1** span labels (page-relative spans decoded through this page table) → **I2** structure-aware chunking (uses the artifact log) → **S2** multimodal (the figure problem).

> 🧭 Coach: one question before the table: "Which later lesson breaks first if the snapshot text changes?" Expected: M1 (gold spans) and C3 (the index manifest refuses a different snapshot_id).

| Often confused | The difference |
|---|---|
| PDF lock vs text snapshot | Lock = sha256 of the PDF bytes. Snapshot = the extracted text, its page table and `snapshot_id`. |
| PyMuPDF page index vs our `page` | `doc[0]` is the first page; `Page.page == 1` for it. |
| `doc_char_*` vs page offsets | Document offsets are canonical; page offsets are derived through the page table. |
| Cleaning vs parser options | Both change the snapshot. Cleaning edits text after extraction (`cleaning` field); an option such as column clipping changes extraction (`options` field). |
| "Same words" vs "same text" | pypdf vs PyMuPDF: 33/33 vs 0/33 on Corpus D (S11). Offsets need the same text. |

---

## Part F — Worked example by hand

Three pages (toy illustration): `"Ice melts.\n"`, `"Seas rise.\n"`, `"Act now.\n"`. Paper only.

**Step 1.** Write `doc_text` and its length.

<details><summary>Answer</summary>

`"Ice melts.\n" + "\n" + "Seas rise.\n" + "\n" + "Act now.\n"`: 11 + 1 + 11 + 1 + 9 = **33** characters (S12). Note the `"\n\n"` at each join.

</details>

**Step 2.** Write the three page-table rows as (page, start, end).

<details><summary>Answer</summary>

(1, 0, 11), (2, 12, 23), (3, 24, 33). Each start = previous end + 1 (S12).

</details>

**Step 3.** Which page and page offset hold document offsets 11, 12 and 17?

<details><summary>Answer</summary>

11 → (1, 11), the join belongs to page 1; 12 → (2, 0); 17 → (2, 5), which is where "rise" starts (S12).

</details>

**Step 4.** Page text `"later extrac-\ntion\n"`. R2 applies (the word "extraction" occurs on another page). Which raw offsets does it delete, and what is the cleaned text?

<details><summary>Answer</summary>

"later " is 6 characters and "extrac" 6 more, so the hyphen is at 12: delete [12, 14) = `"-\n"`. Cleaned: `"later extraction\n"`. The cleaned "t" of "tion" (cleaned offset 12) comes from raw offset 14 (S12).

</details>

> 🧭 Coach: CR-08 probe here, one question: "Page 1 doubles in length (22 characters). What happens to page 2's start, and to the snapshot_id?" Expected: page 2 starts at 23 instead of 12, every later offset shifts by 11, and the id changes because the text hash changes (S12). Then ask what that means for a gold label written before the change.

---

## Part G — Source connection

### G.1 Book (Source A)

| Cite | Book point (paraphrased) | Our assessment |
|---|---|---|
| Ch1 p.4/14 | Step 1: a PDF is parsed page by page into plain text; weak extraction weakens retrieval; the index-card librarian | Right, and the only parsing advice in the book. It says nothing about how |
| Ch1 p.5/14 | Step 3 cleans tabs, extra whitespace and broken line endings; dirty text gives noisy embeddings | Comes **after** Step 2 (split). "Noisy embeddings" is a claim to test (CR-07); v0 does not clean |
| Ch1 p.7/14 | The sketch: load, split, then clean each chunk | Same order as `encode_pdf` L69–L70 |
| Ch2 p.4/11 | A PDF gives one continuous stream; a CSV gives rows | True of `read_pdf_to_string`; v0 keeps pages |
| Ch3 p.1/14 | A retrieved chunk that is a page footer full of links | The symptom of header/footer noise (R1) |
| Ch14 p.5/13 | Each detail chunk is tagged with its page | Page provenance, as in `Page.page` |
| Ch16 p.1/11, p.4/11, p.10/11 | Text extraction skips figures and image tables; extract text and images separately with page tags; captioning is overkill if the parser already gives tables as text | Matches S8. The parser **may** give a table's cells as text, but not its rows (Ch1 p.13/14) |

**Not in the book:** hyphenation, ligatures, two-column order, OCR or scanned pages, named PDF libraries, page numbering, offsets, snapshots (S-src).

### G.2 Repo (Source B), verified at `009adba`

| Location | What it shows | Lesson |
|---|---|---|
| `helper_functions.py:L18-L31` `replace_t_with_space` | replaces `\t` only | Corpus D has 0 tabs, so it is a no-op here (S3). A no-op rule still needs a cleaning version |
| `helper_functions.py:L48-L76` `encode_pdf` | `PyPDFLoader(path).load()` (L62–L63), split (L69), **then** clean (L70) | Cleaning after splitting breaks "chunk text = slice of stored text" |
| `helper_functions.py:L223-L245` `read_pdf_to_string` | `fitz.open` (L237), `content += page.get_text()` (L244) | Pages glued, page numbers lost (S4) |
| `simple_rag.ipynb` cell 10 | the notebook's own `encode_pdf`, same loader and order | As above |
| `multi_model_rag_with_captioning.ipynb` cell 8 | two empty lists only | — |
| `multi_model_rag_with_captioning.ipynb` cell 9 | PyMuPDF `get_text().strip()`, `page_number+1`, `get_images(full=True)` | Keeps 1-based pages; `.strip()` shifts offsets. Its PDF is not in the repo |

No repo code de-hyphenates, normalises ligatures, removes headers/footers or calls `find_tables` (S-src).

**Corrections to the [04 C1 row](../04_BOOK_TO_CODE_MAPPING.md)** (04 is not edited):
1. "What the book contributes: parse page by page; **clean before chunking**". The book cleans **after** chunking (Ch1 p.4–5/14, p.7/14).
2. `multi_model_rag_with_captioning.ipynb` "cells 8–9": cell 8 only creates two lists; the extraction is cell 9, which also strips each page.
3. The proposed experiment needs "one two-column arXiv PDF" and pypdf. Neither is in the project (no two-column PDF on disk; pypdf is not a project dependency). This lesson uses the zoo for two columns and a scratch environment for pypdf (S11).
4. "Headers/footers … absent in both": the code has none, but the book shows the symptom (Ch3 p.1/14). Book column should add Ch1 p.7/14 and Ch16 p.1/11, p.10/11.

---

## Part H — Implementation progression

### H.1 The lab: [`labs/C1_parsing_lab.ipynb`](../labs/C1_parsing_lab.ipynb) (blank-file first)

The notebook has tasks, empty code cells, prediction cells and CHECK cells. It has **no solution code**; CHECK cells compare fingerprints.

| # | Task | The checks test |
|---|---|---|
| 1 | `load_pages` → 33 `Page` records | 1-based pages, raw text, parser string, pinned 1.26.7 |
| 2 | `build_page_table` → `doc_text`, rows | 72,593 characters; every slice round-trips |
| 3 | `snapshot_id` from 06 §5.3 | `ea07572562ac`; version and cleaning change it |
| 4 | Write the manifest and text; `validate_snapshot` | File bytes hash = `doc_text_sha256`; a shifted page table is rejected |
| 5 | `page_of` | The join rule; "Paris Agreement" → page 6 |
| 6 | `artifact_counts`, `repeated_lines` on Corpus D | S5 values |
| 7 | Diagnose the zoo | Interleaved columns, column fix, tables, empty vs image-only, ligatures |
| 8 | `plan_edits`, `apply_edits`, `undo_edits` | Zoo edits; round trip; 0 edits on D vs 7 naive |
| 9 | Book Ch1 p.2 and p.13 as specimens | Figure text lost; table not detected |

API names you may look up: `pymupdf.open`, `page.get_text`, `clip=`, `page.get_images`, `page.get_image_rects`, `page.find_tables`, `unicodedata.normalize`, `bisect.bisect_right`, `hashlib.sha256`. The reference implementation is `sources/verification/C1/c1_ref.py`.

> 🧭 Coach: The reference file is a **solution**. Do not show it before an attempt plus a hint (CR-04). Grade `coding_independence_0_3` on Tasks 1, 2, 3, 5 and `debugging_0_3` on any failing CHECK the learner fixes, and on Task 4 (the Windows newline).

### H.2 Repo reading guide (answer before opening)

Open `helper_functions.py` at L48 and L223.
1. Which line loads the PDF in `encode_pdf`, and which library is behind it?
2. On which line is the text cleaned, and is that before or after splitting?
3. What separator does `read_pdf_to_string` put between pages?
4. How would you find the page of character 50,000 in its output?

<details><summary>Answers</summary>

1. L62 `PyPDFLoader(path)`, which wraps pypdf.
2. L70, after the split on L69.
3. None: `content += page.get_text()` (L244). PyMuPDF page texts end with `"\n"` on Corpus D, so words do not merge, but page boundaries are not recorded.
4. You cannot from the string alone. You would need the page lengths, which the function throws away.

</details>

### H.3 Reusable design (future `ragkit/loaders.py`; nothing is created now)

- `load_pdf(path, doc_id) -> list[Page]`, raw `get_text()`, `parser=f"pymupdf {VersionBind}"`.
- `build_snapshot(corpus, docs) -> manifest` with the exact 06 §5.3 fields and recipe; text written with `newline="\n"`.
- `validate_snapshot` runs before any chunking or scoring (fail closed, 06 §5.3 rule 4).
- `artifact_report(pages) -> dict` and `plan_edits` run as **reports**; a cleaning step is a config value (`cleaning:`), never a default.

### H.4 Corpus T: pending

The make-up of Corpus T is decided (D-01/D-02: 3–4 RAG papers plus 2 non-RAG papers, at least one two-column PDF with tables). The **file list is not chosen**; 06 §5.1 names candidates (Lewis et al. 2020, DPR, HyDE, Lost in the Middle, RAPTOR). When the learner chooses: hash and lock the PDFs ([06 §5.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#53-corpus-freezing)), rerun lab Tasks 1–8 on each file, and save the artifact log (before/after snippets, page, raw offsets) as the 02 evidence. No numbers about T exist yet.

### H.5 Interface handed to C2 and C3 (exact shape)

| Object | Shape |
|---|---|
| `pages` | `list[Page]`, `Page(doc_id: str, page: int, text: str, parser: str)`, frozen dataclass; Corpus D: 33 records, `doc_id="climate"`, `page` 1..33, `text` = raw `page.get_text()`, `parser="pymupdf 1.26.7"` |
| `doc_text` | `"\n".join(p.text for p in pages)`: 72,593 characters, sha256 `5106772e…` |
| `rows` (page table) | `[{"page", "doc_char_start", "doc_char_end", "text_sha256"}]`, ends exclusive, start = previous end + 1 |
| manifest | `evaluation/snapshots/D_ea07572562ac.json` (06 §5.3 fields; `json.dumps(indent=2, ensure_ascii=False)`, UTF-8) |
| snapshot text | `evaluation/snapshots/ea07572562ac/climate.txt` (UTF-8, `"\n"` newlines; git-ignored by `.gitignore`) |
| `snapshot_id` | `ea07572562ac` (parser `pymupdf@1.26.7`, options `{}`, cleaning `none`) |

C2's lab re-extracts the same pages in its setup cell and stops unless it gets `ea07572562ac` (`sources/verification/C2lab/c2_setup.py`), so C1 and C2 agree by construction. Chunks (C2/C3) carry this `snapshot_id`; a page's text is `doc_text[row["doc_char_start"]:row["doc_char_end"]]`.

---

## Part I — Controlled experiment

**n/a for C1.** The card defines no pipeline variable to compare on the eval set. 04's "PyMuPDF vs pypdf, hand-count artifacts" is an observation, done here for Corpus D (S11) and pending for Corpus T (H.4). Whether any cleaning rule improves retrieval is unknown until a later version tests it.

---

## Part J — Failure and debugging

For each: write your predicted cause and fix, then open. Each diagnosis says whether it is a **retrieval** or a **generation** failure (CR-11).

**J1. Citations off by one page.** Answers cite `[climate:5]` for text that is on page 6.

<details><summary>Diagnosis</summary>

- **Cause.** A 0-based page index stored as the page number (PyMuPDF's `doc[i]`, or PyPDFLoader's `page` metadata).
- **Kind.** Neither retrieval nor generation quality: a provenance bug. Citation checks (v5) will flag it.
- **Fix.** Store `i + 1`; assert `pages[0].page == 1`.

</details>

**J2. Gold labels match nothing after a rebuild.** Every coverage score is 0; no error.

<details><summary>Diagnosis</summary>

- **Cause.** The text changed (another reader, version, option or cleaning) but the labels kept their old offsets.
- **Kind.** Evaluation failure that looks like a retrieval failure.
- **Fix.** Compare `snapshot_id`s first; fail closed on a mismatch (06 §5.3 rule 4).

</details>

**J3. The snapshot hash fails only on Windows.**

<details><summary>Diagnosis</summary>

- **Cause.** Text written with default newlines: `"\n"` became `"\r\n"` (73,727 vs 72,595 bytes, S7).
- **Kind.** Infrastructure.
- **Fix.** `open(path, "w", encoding="utf-8", newline="\n")`; hash the bytes in a test.

</details>

**J4. Top-k is full of the same footer.** Many chunks end with "Page 12", "Page 13", ….

<details><summary>Diagnosis</summary>

- **Cause.** Repeated header/footer lines embedded with every chunk (the book's Ch3 p.1/14 symptom).
- **Kind.** Retrieval.
- **Fix.** Measure first (R1 report); if adopted, clean before chunking as a new snapshot, then compare retrieval metrics on the same questions.

</details>

**J5. A two-column paper gives nonsense sentences.**

<details><summary>Diagnosis</summary>

- **Cause.** Lines read across columns (zoo S9). De-hyphenation on top makes it worse ("extracreading").
- **Kind.** Retrieval (and then generation, because the context is garbled).
- **Fix.** Column-aware extraction (an `options` change ⇒ new snapshot); check reading order by eye on a sample.

</details>

> 🧭 Coach: For J1 and J3, ask for the **one-line assert** that would have caught it. It counts as evidence for `debugging_0_3`.

---

## Part K — Engineering decisions

| Question | Decision | Why |
|---|---|---|
| Which reader? | PyMuPDF `page.get_text()`, pinned 1.26.7 | 06 §3.1; text and id reproducible |
| Page numbers | 1-based `page` in every record | Citations and humans count from 1 |
| Coordinates | Document offsets into `doc_text`, pages joined with `"\n"` | One system for chunks and gold spans |
| Cleaning in v0 | None; run R1–R3 as **logged reports** | Offsets stay raw; the rules change nothing on D (S10) |
| When cleaning is adopted | Before chunking, with a cleaning version | It is then part of the snapshot |
| Columns, tables, figures | Detect and flag; no fix in v0 | Not present in Corpus D; T decides |
| Writing files | UTF-8, `newline="\n"`, validate before use | S7; 06 §5.3 rule 4 |

**When NOT to clean:** when the rule cannot be shown to help on your questions, when it would change offsets that labels already use, or when its false positives are unknown (R1 on `index.pdf`, S8).

---

## Part L — Assessment

One short question per item. Each has a reply template. Score with [05 §4.2](../05_LEARNING_AND_RETENTION_SYSTEM.md#42-graded-rubrics-04).

> 🧭 Coach: Ask one item at a time, with its template. Never put two questions in one turn. Record confidence first.

### L.1 Recall

**C1-R-01.** What four fields does a v0 page record have?
*Template:* "`Page(____, ____, ____, ____)`."

<details><summary>Criteria for 4</summary>

`doc_id`, `page` (1-based), `text` (raw `get_text()`), `parser` ("pymupdf 1.26.7"). Plus why: provenance for citations and a parser record for the snapshot.

</details>

**C1-R-02.** What goes into the `snapshot_id`?
*Template:* "The parser ____, its ____, the ____, the cleaning ____, the page join, and each document's ____."

<details><summary>Criteria for 4</summary>

Backend and version, options, cleaning version, `page_join`, and each `doc_id` with its `doc_text_sha256` (06 §5.3). Plus the boundary: a new version changes the id even with identical text (S3).

</details>

**C1-R-03.** Why does v0 do no cleaning?
*Template:* "Because offsets must ____, and any cleaning would ____."

<details><summary>Criteria for 4</summary>

Chunks and gold spans refer to the raw snapshot; cleaning creates a new snapshot and must be justified by measurement. Plus evidence: on Corpus D the rules change nothing and naive de-hyphenation would damage 7 of 7 words (S5, S10).

</details>

**C1-R-04.** Name four extraction artifacts.
*Template:* "____, ____, ____ and ____."

<details><summary>Criteria for 4</summary>

Four of D.4's eight, each with how to detect it (e.g. two columns: lines alternate; image-only page: empty text but an image).

</details>

### L.2 Application

**C1-A-01.** Pages of 100, 50 and 80 characters. Where does page 3 start in `doc_text`?
*Template:* "Start = ____ + ____ + ____ = ____."

<details><summary>Criteria for 4</summary>

100 + 1 + 50 + 1 = **152** (derived). Self-check: total length 100 + 50 + 80 + 2 = 232, and page 3 ends at 152 + 80 = 232.

</details>

**C1-A-02** (CR-08). The PDF gains one extra page at the end. Which page-table rows change, and does the `snapshot_id` change?
*Template:* "Rows ____ stay the same; ____ is added; the id ____ because ____."

<details><summary>Criteria for 4</summary>

All existing rows stay the same (offsets only grow at the end); one row is added; the id changes because `doc_text_sha256` changes. Labels on old pages still decode, but the dataset must be rebound to the new snapshot (06 §5.3 rule 3).

</details>

**C1-A-03** (debugging). What is wrong here?

```python
pages = [Page("climate", i, p.get_text().strip(), "pymupdf") for i, p in enumerate(doc)]
```

*Template:* "The bugs are ____, ____ and ____."

<details><summary>Criteria for 4</summary>

0-based page numbers; `.strip()` changes the text (70 characters on Corpus D, S4), so the hash and offsets differ; the parser string lacks the version. Fix each; assert `pages[0].page == 1`.

</details>

### L.3 Transfer

> 🧭 Coach: C1-T-01 is a practice item. For the scored CR-13 item, invent a fresh scenario (another document type, language, layout or constraint) that is not in this file, and grade it with the Transfer rubric.

**C1-T-01.** A colleague's slide decks are exported to PDF. Many slides are pictures with a few words on top. What do you check first?
*Template:* "I would check ____, because ____. I would measure it by ____."

<details><summary>Criteria for 4</summary>

- Count characters and images per page; flag image-only or near-empty pages (S9's empty vs image-only test). Check reading order on a sample of slides by eye.
- Trade-off: OCR or captioning adds cost and new errors (Ch16 p.10/11 says when it is overkill).
- Verify by measurement: what fraction of gold answers lie on flagged pages; retrieval metrics on those questions, kept separate from answer quality.
- When not to: if no questions target the image content.

</details>

### L.4 When is C1 mastered?

- **`applied` (L3):** C1-R-01 or C1-R-02 ≥ 3 on two different days, one ≥ 24 h after teaching; two Application items ≥ 3; `coding_independence_0_3 ≥ 2` on lab Tasks 1, 2, 3, 5.
- **`transfer` (L4):** a fresh novel-scenario item ≥ 3; `debugging_0_3 ≥ 2`; the Corpus T artifact log once T exists.

---

## Part M — Retention

### M.1 Flashcards

| # | Front (one question) | Back |
|---|---|---|
| 1 | First page number in our records? | 1 |
| 2 | How are pages joined? | `"\n"`; next start = previous end + 1 |
| 3 | Who owns the join character? | The page before it |
| 4 | Corpus D `snapshot_id`? | `ea07572562ac` |
| 5 | Same text, newer pymupdf: same id? | No: the version is in the recipe |
| 6 | v0 cleaning? | None |
| 7 | Line-end hyphens in Corpus D? | 7, all real compounds |
| 8 | Blank page vs scanned page in `get_text()`? | Both `""`; check images |
| 9 | Windows file write? | `newline="\n"` |
| 10 | Which repo reader loses pages? | `read_pdf_to_string` |

### M.2 Retrieval practice (closed book; log per [05 §5.1](../05_LEARNING_AND_RETENTION_SYSTEM.md#51-active-recall-what-a-review-item-looks-like))

| When | One question | Template |
|---|---|---|
| Day 1 | What are the four `Page` fields? | "`Page(____)`" |
| Day 3 | What changes the `snapshot_id`? | "Any change to ____." |
| Day 7 | Pages of 10, 20 and 30 characters: where does page 3 start? (Answer: 32; derived) | "10 + 1 + ____ + 1 = ____" |
| Day 14 | When would you adopt a cleaning rule? | "Only when ____, and then ____." |

### M.3 Teach-back prompt ([05 §5.4](../05_LEARNING_AND_RETENTION_SYSTEM.md#54-teach-back-protocol))

"In 3 minutes, explain to a teammate how a PDF becomes v0's frozen snapshot, and why we do not clean it." A 4 needs: page records with 1-based pages; one joined text with a page table; the `snapshot_id` recipe inputs; two measured artifacts; the reason for no cleaning; the Windows newline trap.

### M.4 Interleaving links

- **C2:** `doc_text` has `"\n\n"` only at the 32 page joins (S2). What does the recursive splitter do with that, per page and across pages?
- **P1:** 1,093 of Corpus D's 1,100 lines end with a space (S5). Would stripping those spaces change token counts much? Predict, then count.
- **M1:** decode a page-relative gold span through the page table.

### M.5 Misconception-log entries to add when observed

| Label | Correct model (short) | Root cause | Severity | Check items |
|---|---|---|---|---|
| "Cleaning can only help" | It changes offsets and can damage words (7/7 on D) | over-generalisation | high | C1-A4, C1-R-03 |
| "Same words = same text" | Offsets need byte-identical text | terminology | medium | C1-A5, J2 |
| "Page index = page number" | 0-based index, 1-based page | off-by-one | medium | J1, C1-A-03 |

### M.6 Progress-tracker entry (format only; fictional values, per [05 §6.1](../05_LEARNING_AND_RETENTION_SYSTEM.md#61-progressconcept_trackercsv))

```csv
C1,Document loading & parsing,2,E,exposed,<YYYY-MM-DD>,,,<YYYY-MM-DD +1>,1,,,,,,,na,,1,log:<YYYY-MM-DD>#C1-R-01
```

---

## Source references

**Book (Source A).** Ch1 p.2/14 (specimen), p.4/14, p.5/14, p.7/14, p.13/14 (specimen); Ch2 p.4/11; Ch3 p.1/14; Ch14 p.5/13; Ch16 p.1/11, p.4/11, p.5/11, p.10/11; `intro.pdf` and `index.pdf` (specimens). Checked against the PyMuPDF page text by `c1_sources.py`. Paraphrased; no quotation reaches 15 words.

**Repo (Source B)**, `NirDiamant/RAG_Techniques` @ `009adba2be1bef49780ef73b6dd3c18fd24b035b`, cells 0-based: `helper_functions.py` L1, L10, L18–L31, L48, L62–L63, L69–L70, L76, L223, L237–L238, L244–L245; `all_rag_techniques/simple_rag.ipynb` cell 10; `all_rag_techniques/multi_model_rag_with_captioning.ipynb` cells 8, 9; `data/Understanding_Climate_Change.pdf` (sha256 `1d58a0fa…92669`, 206,372 bytes).

**Our records.** [06 §2.3, §2.4, §3.1, §5.1, §5.3](../06_RAG_PROJECT_AND_EVALUATION_PLAN.md#53-corpus-freezing); [07 H.3](../07_SAMPLE_LESSON.md) (`page_of`); [LAB_FACTS §0, §7](../sources/verification/LAB_FACTS.md); 08 D-01, D-02, RK-18; [`sources/verification/C2lab/c2_setup.py`](../sources/verification/C2lab/c2_setup.py) (the C2 lab's copy of the recipe).

---

## Verification log

**Environment.** Run on 2026-10-08 with `uv run` from `rag_learning/`: CPython 3.12.8, pymupdf 1.26.7. A throwaway venv in the session scratchpad (outside the workspace) held pymupdf 1.28.2 and pypdf 6.19.0 for S11 only; nothing was installed into the project env. No Groq or Cohere call; `.env` not read.

| Claim | How verified |
|---|---|
| All S1–S10, S12 numbers | **Ran** `c1_measure.py`; output `out_c1_measure.txt`; a second run was **byte-identical** |
| `snapshot_id` = `ea07572562ac` | **Ran** S2 (transcribed 06 recipe); equals 06 §5.3, the acceptance suite (145/145 re-run 2026-10-08) and `C2lab/c2_setup.py` (same parts, read) |
| S11 (pymupdf 1.28.2 and pypdf) | **Ran** `c1_crossversion.py` in both environments |
| Every repo line/cell, book page, repo-wide count and book absence | **Ran** `c1_sources.py`: ALL PASS |
| Lab CHECK cells | **Ran** with a throwaway solution outside the workspace: 9/9 pass (runner and a real Jupyter kernel); 9 broken variants each fail at the intended CHECK; an empty run fails 9/9 without crashing |
| 04 C1 row | Four corrections (G.2) |

**Interface assumptions** (06 is not explicit; most literal reading taken):
1. `Page` is a frozen dataclass with fields in the order `doc_id, page, text, parser`, and `parser` is the string `"pymupdf <VersionBind>"` (06 §3.1 writes `Page(doc_id, page=1-based, text, parser="pymupdf <version>")`).
2. The manifest's `parser.call` is `"page.get_text()"` (06 §5.3 manifest), while 06 §2.4/§3.1 write `get_text("text")`: identical output on 33/33 pages (S4).
3. Manifest file bytes are `json.dumps(manifest, indent=2, ensure_ascii=False)` in UTF-8, as in the acceptance suite; `created_utc` is set at write time and is not an input of the id.
4. Snapshot text files use `"\n"` newlines on disk, so the file's sha256 equals `doc_text_sha256` (06 says `newline: "\n"`; it does not say how to write on Windows).

**Still UNVERIFIED:**
- the cause of the 37-character gap between `PyPDFLoader` (72,523, LAB_FACTS) and raw pypdf `extract_text()` (72,560);
- whether PyMuPDF 1.28.2 gives identical text on PDFs other than Corpus D;
- every artifact count for Corpus T (files not chosen);
- whether any cleaning rule changes retrieval quality (no experiment run);
- the layout of `attention_is_all_you_need.pdf` used by the captioning notebook (not in the repo).
