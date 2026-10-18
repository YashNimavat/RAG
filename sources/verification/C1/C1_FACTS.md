# C1_FACTS — what the C1 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/C1_document_parsing.md`](../../../concepts/C1_document_parsing.md) is listed here with the command and output section that produced it. Numbers not produced by these runs are marked CITED (from an earlier logged run), DERIVED (arithmetic shown in the lesson) or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`), **pymupdf 1.26.7** (pinned).
- **Second environment (S11 only).** A throwaway venv in the session scratchpad, **outside the workspace**, created with `uv venv` + `uv pip install pypdf==6.19.0 pymupdf==1.28.2`. Nothing was installed into the project env. pypdf 6.19.0 is the version behind the 07 lab's PyPDFLoader numbers (LAB_FACTS §0).
- **Inputs.** Corpus D `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf` (sha256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`, 206,372 bytes, 33 pages). Book PDFs read-only, used as **specimens** (not a corpus). The synthetic zoo PDF is generated into the scratch directory by `c1_zoo.py` (TOY ILLUSTRATION).
- **No API calls.** No Groq or Cohere call; `.env` never read.
- **Scripts** (this folder):

  | Script | Produces | Saved output |
  |---|---|---|
  | `c1_ref.py` | Reference implementation (Page, page table, `snapshot_id`, `validate_snapshot`, `page_of`, artifact counts, logged cleaning R1–R3, column extraction). **A solution for the lab** | — |
  | `c1_zoo.py` | The synthetic artifact zoo (5 pages); copied verbatim into the lab's setup cell | — |
  | `c1_measure.py` | S1–S10, S12 | `out_c1_measure.txt` (stdout; includes one PyMuPDF advisory line "Consider using the pymupdf_layout package…"), `out_c1_measure.stderr.txt` (empty) |
  | `c1_crossversion.py` | S11 (pymupdf 1.28.2, pypdf 6.19.0) | `out_c1_crossversion_project.txt`, `out_c1_crossversion_scratchenv.txt` |
  | `c1_sources.py` | S-src: repo lines/cells, repo-wide counts, book pages, book absences | `out_c1_sources.txt` (ALL PASS) |
  | `c1_build_lab.py` | `labs/C1_parsing_lab.ipynb`, with fingerprints computed from `c1_ref.py` | `out_c1_build_lab.txt` |
  | `c1_lab_runner.py` | Runs the lab with learner cells taken from a solutions file | `out_c1_labtest_good.txt`, `out_c1_labtest_broken.txt`, `out_c1_labtest_empty.txt`; `out_c1_labtest_kernel.txt` (real Jupyter kernel; driver script in the scratchpad) |

- **Re-run** (from `rag_learning/`, Git Bash; `<scratch>` is any directory outside the workspace):
  ```bash
  B="C:/Yash/New-Work/Book RAG"; V=sources/verification/C1; P="$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
  PYTHONIOENCODING=utf-8 uv run python $V/c1_measure.py "$B" <scratch> > $V/out_c1_measure.txt 2> $V/out_c1_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python $V/c1_sources.py "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" > $V/out_c1_sources.txt
  PYTHONIOENCODING=utf-8 uv run python $V/c1_crossversion.py "$P" > $V/out_c1_crossversion_project.txt
  PYTHONIOENCODING=utf-8 <scratch venv>/Scripts/python.exe -I $V/c1_crossversion.py "$P" > $V/out_c1_crossversion_scratchenv.txt
  PYTHONIOENCODING=utf-8 uv run python $V/c1_build_lab.py "$B" labs/C1_parsing_lab.ipynb > $V/out_c1_build_lab.txt
  PYTHONIOENCODING=utf-8 uv run python $V/c1_lab_runner.py labs/C1_parsing_lab.ipynb <solutions file outside the workspace> <scratch>/snap
  ```
- **Determinism.** Two consecutive runs of `c1_measure.py` gave **byte-identical** stdout (`cmp`).
- **Acceptance suite** re-run the same day: `contracts_check.py` → **145 passed, 0 failed**.

## 1. Facts by section (`M` = `c1_measure.py`, `X` = `c1_crossversion.py`, `S` = `c1_sources.py`)

### S1 Inputs (M)
| Fact | Value |
|---|---|
| pymupdf | 1.26.7 (`fitz.VersionBind`) |
| Corpus D | sha256 `1d58a0fa…92669`, 206,372 bytes, 33 pages |
| Book `chapter 1.pdf` | 14 pages (sha256 prefix `2036e581edb94c14`) |

### S2 Corpus D pages, `doc_text`, page table, `snapshot_id` (M)
| Fact | Value |
|---|---|
| Pages / first and last `page` | 33 / 1 and 33 |
| Page lengths | min 636 (p.33), max 2,494 (p.19); full list in the output |
| Sum of page lengths | 72,561 |
| `len(doc_text)` (joined with `"\n"`) | 72,593 (= sum + 32) |
| `doc_text_sha256` | `5106772efa77003b0d6c79bc1a429b8dacf244d9556f412bae1c4fe6bc7368c6` |
| Rows | p.1 [0, 2,424); p.2 [2,425, 4,835); p.3 [4,836, 7,019); p.8 start 16,074; p.10 20,555; p.23 49,209; p.29 62,565; p.33 [71,957, 72,593) |
| Round trip `doc_text[s:e] == page` | True, all pages |
| Every page ends with `"\n"` | True |
| `"\n\n"` in `doc_text` / at page joins | 32 / 32 |
| `snapshot_id` | **`ea07572562ac`** = 06 §5.3. The C2 lab's setup (`sources/verification/C2lab/c2_setup.py` L24–L28) uses the same parts and asserts the same id |

### S3 What changes the id (M; same recipe, one input changed)
| Change | id |
|---|---|
| version 1.28.2, same text | `4b7e61b9e418` |
| cleaning `tabs_v1`, same text | `6164dfc95324` |
| options `{"sort": true}`, same text | `f1e46e7c3c68` |
| one extra space at end of page 1 | `a79df757e413` |
| `page_join` as a real newline | `5ad6acfd28ec` |
| Tabs in Corpus D / `replace_t_with_space` changes text | 0 / False |

### S4 Other calls on Corpus D (M)
| Fact | Value |
|---|---|
| `get_text("text") == get_text()` | 33/33 pages |
| `get_text(sort=True)` differs / same after whitespace collapse | 33 / 33 of 33 |
| Distinct text-block x0 / images / `find_tables` | [72] / 0 / 0 |
| `read_pdf_to_string` length | 72,561; page 2 at 2,424 (vs 2,425); page 33 at 71,925 (vs 71,957) |
| `.strip()` per page (captioning cell 9) | 72,491 characters; 70 removed |

### S5 Corpus D artifact inventory (M)
| Fact | Value |
|---|---|
| Empty pages / ligatures / soft hyphens / tabs / `"\n\n"` inside pages | [] / 0 / 0 / 0 / 0 |
| Lines / ending with a space | 1,100 / 1,093 |
| Non-ASCII | one `—` (p.19) |
| Line-end hyphen breaks | 7: p.8 cost-competitive, p.11 well-being, p.12 Public-private, p.19 well-being, p.29 market-based, p.29 climate-friendly, p.31 decision-making. Joined form attested elsewhere: 0/7; hyphenated form attested: 7/7 |
| Repeated lines | threshold 17: none; even at ≥ 3 pages: none |
| Page breaks not ending in `. ! ? : " ) '` | 24 of 32 |
| … next page starts lowercase | 8: 12→13, 14→15, 15→16, 16→17, 21→22, 22→23, 24→25, 28→29 (same pages as LAB_FACTS §7, PyPDFLoader) |

### S6 Offsets → pages (M)
| Fact | Value |
|---|---|
| First "Paris Agreement" | doc offset 13,420 → page 6, page offset 1,874 |
| Pages / occurrences | [6, 10, 23, 24] / 8 |
| Offsets 2,424 / 2,425 / 0 / 72,592 | (1, 2,424) / (2, 0) / (1, 0) / (33, 635) |

### S7 Writing the snapshot on Windows (M)
| Fact | Value |
|---|---|
| `os.linesep`; newlines in `doc_text`; UTF-8 bytes | `'\r\n'`; 1,132; 72,595 |
| Default `open(..., "w")`: bytes / hash = `doc_text_sha256` | 73,727 / False |
| `newline="\n"`: bytes / hash equal | 72,595 / True |
| Read back default file in text mode = `doc_text` / with `newline=''` | True / False |
| Manifest validates; page 2 shifted by +1 | yes; rejected ("start != previous end + len(page_join)") |

### S8 Book specimens (M)
| Fact | Value |
|---|---|
| Ch1 chars per page | 1406, 679, 710, 1269, 1108, 1125, 890, 1251, 908, 858, 1047, 1410, 1288, 233 |
| Ch1 images per page | 1 on pages 2, 3, 5, 6, 7, 9, 10, 11; 0 elsewhere |
| `•` characters in Ch1 text | 0 |
| Ch1 p.2: text blocks intersecting the image | 0 |
| Ch1 p.13: `find_tables()` default / `strategy="text"` | 0 / 1 (45 × 9 cells; first cells "Fac", "tor", "Impact") |
| Ch1 p.13 first lines | Factor · Impact · Latency · (cell text) … one cell per line |
| `intro.pdf` (8 pages, threshold 4) | one website-name footer line flagged, on 4 pages |
| `index.pdf` (6 pages, threshold 3) | 5 real section titles flagged, 6 pages each (false positives) |

### S9 Zoo (M; TOY ILLUSTRATION)
| Fact | Value |
|---|---|
| Chars per page / images per page | 273, 74, 0, 0, 101 / 0, 0, 0, 1, 0 |
| p.1 default order | header, footer ("Page 1" second), then L1 R1 L2 R2 L3 R3 L4 R4, then the ligature line |
| `sort=True` | both columns on one line |
| Column clipping | true reading order |
| `TEXT_DEHYPHENATE` default order / with clip | "by any later extracreading order must follow" / "by any later extraction or retrieval step." |
| Ligatures / "file" found / after NFKC / without `TEXT_PRESERVE_LIGATURES` | 3 / False / True / 0 ligature chars |
| `TEXTFLAGS_TEXT` includes PRESERVE_LIGATURES / DEHYPHENATE | True / False |
| p.2 `get_text()` / `find_tables()` | one cell per line / 1 table, 3 × 2, correct |
| p.3 / p.4 | `''`, 0 images / `''`, 1 image |
| Repeated lines (threshold 3) | "ACME Technical Report", "Page #" (3 pages each) |

### S10 Logged cleaning R1–R3 (M)
| Fact | Value |
|---|---|
| Zoo edits (page 1 by columns) | R1 6, R2 1, R3 3; raw characters removed 92, inserted 6 |
| R2 edit | page 1 [107, 109) `"-\n"` → `""` |
| Cleaned "extraction" | raw page offsets 101–112 |
| Round trip `undo(apply(edits)) == raw` | True on every page |
| Corpus D edits / naive `-\n` join | 0 / 7 |

### S11 Other parser and version (X)
| Fact | Value |
|---|---|
| pymupdf 1.28.2 `doc_text_sha256` = 1.26.7 value | True (byte-identical text) |
| pypdf 6.19.0 `extract_text` joined | 72,560 characters |
| pypdf vs pymupdf: identical pages / same word sequence | 0 / 33 of 33 |
| pymupdf page == pypdf page + `"\n"` | 33/33 |
| pypdf lines ending with space | 1,093 of 1,100 |
| CITED: PyPDFLoader total (07 lab) | 72,523 (LAB_FACTS §7); `page` metadata 0-based |
| Cause of the 37-character gap PyPDFLoader vs raw pypdf | **UNVERIFIED** on 2026-10-08; settled 2026-10-18 by K2 (per-page `.strip()`) |

### S12 Part F toy (M; TOY ILLUSTRATION)
`["Ice melts.\n", "Seas rise.\n", "Act now.\n"]`: `doc_text` 33 chars; rows (1, 0, 11), (2, 12, 23), (3, 24, 33); page_of 10 → (1, 10), 11 → (1, 11), 12 → (2, 0), 17 → (2, 5), 30 → (3, 6). Page 1 doubled: page 2 starts at 23, length 44, id changes. `"later extrac-\ntion\n"` with "extraction" on another page: R2 edit [12, 14); cleaned `"later extraction\n"`, cleaned offset 12 ← raw 14.

### S-src Sources (S): ALL PASS
- Repo HEAD `009adba2…`. `helper_functions.py` L1, L10, L18, L30–L31, L48, L62–L63, L69–L70, L76, L223, L237–L238, L244–L245 as quoted in the lesson.
- `simple_rag.ipynb` cell 10 (PyPDFLoader, split, then `replace_t_with_space`); `multi_model_rag_with_captioning.ipynb` cell 8 (two empty lists only), cell 9 (`fitz.open('attention_is_all_you_need.pdf')`, `get_text().strip()`, `page_number+1`, `get_images(full=True)`); that PDF is not in the repo.
- Repo-wide code matches: PyPDFLoader 23, `read_pdf_to_string` 8, SimpleDirectoryReader 14, `fitz.open` 2, `get_text(` 2, `replace_t_with_space` 9. No hyphenation, ligature/Unicode normalisation, header/footer or `find_tables` code.
- Book pages and phrases (each < 15 words): Ch1 p.2, 4, 5, 7, 13/14; Ch2 p.4/11; Ch3 p.1/14; Ch14 p.5/13; Ch16 p.1, 4, 5, 10/11. Ch1 p.7 sketch: split (2) before clean (3).
- Book absences (all pages): hyphen*, ligature, OCR, two-column / multi-column / reading order, PyMuPDF / pypdf / fitz, scanned, snapshot.

### Lab test
| Run | Result |
|---|---|
| Good throwaway solution (scratchpad), runner | 9/9 CHECK pass |
| Same, real Jupyter kernel (project `.venv`) | 9/9 |
| Empty solutions | 0/9, no crash |
| Broken variants (each fails at the intended CHECK) | 0-based pages → T1; no join offset → T2 (+T4, T5 cascade); real newline in recipe → T3; plain `open` on Windows → T4; validate only the doc hash → T4; join char to next page → T5; lines by `split("\n")` → T6; columns by `sort=True` → T7 (+T8); naive de-hyphenation → T8 |

## 1b. Added 2026-10-18: K1–K12 (`c1_kit_measure.py`) for the HTML lesson

`K` = `c1_kit_measure.py` (section in `out_c1_kit_measure.txt`). Run from `rag_learning/`:
`PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_kit_measure.py "C:/Yash/New-Work/Book RAG" <scratch dir>`. A second run gave byte-identical stdout (`cmp`); stderr is empty. The stdout contains PyMuPDF's advisory line "Consider using the pymupdf_layout package…" once (research E-C1-8: that package cannot be installed next to the 1.26.7 pin). Same Corpus D, pin and `c1_ref.py` functions as S1–S12; no book PDF is opened; no API call, no `.env` read. `c1_measure.py` and its output are unchanged.

| Id | Fact | Value |
|---|---|---|
| K1 | Environment | Python 3.12.8; pymupdf 1.26.7; Unicode database 15.0.0 |
| K2 | **The 37-character PyPDFLoader gap is per-page `.strip()`** (settles S11's UNVERIFIED and research E-C1-7) | PyMuPDF pages sum 72,561; minus each page's final `"\n"` (= the pypdf pages, S11) 72,528, joined 72,560; `.strip()` per page sum 72,491, joined with `"\n"` **72,523 = LAB_FACTS §7's PyPDFLoader `full_len`** (that run joined `page_content` with `"\n"`). Removed: 37 vs pypdf (all trailing whitespace before the final newline; 0 leading), 70 vs PyMuPDF. DERIVED from S11's equality, so it holds for pypdf 6.19.0 on Corpus D |
| K3 | Characters, UTF-8 bytes, NFKC (literal strings) | `ﬁ` U+FB01: 3 bytes, NFKC `fi` (+1) · `ﬂ` +1 · `…` 3 bytes, `...` (+2) · `½` 2 bytes, `1⁄2` (+2) · `x²` → `x2` (+0, the exponent is lost) · `é` one code point (2 bytes) unchanged · `e` + U+0301 (3 bytes) → `é` (−1) · `—` 3 bytes, unchanged · soft hyphen U+00AD unchanged · no-break space U+00A0 → space (+0). "file" in "The ﬁle": False; after NFKC: True. **Corpus D: 0 characters NFKC would change, delta 0**; 72,593 characters, 72,595 UTF-8 bytes; only non-ASCII character `—` |
| K4 | Offset shift (TOY, 520 characters, ligatures at raw 100 and 300) | After NFKC: 522 characters; raw offset 500 lands at **502**, same character; one ligature shifts every later offset by +1; map: cleaned 101 ← raw 100, cleaned 102 ← raw 101, cleaned 502 ← raw 500 |
| K5 | A hash names exact bytes (TOY) | `"Seas rise.\n"` `63c2941c7f6b` · one extra space `b1e07b17c9c7` · `"\r\n"` `a71b05c14df5` · lower-case s `2d04a7947fc7` (sha256, first 12 hex) |
| K6 | PyMuPDF flags (installed source) | `TEXTFLAGS_TEXT` = 195: PRESERVE_LIGATURES, PRESERVE_WHITESPACE, MEDIABOX_CLIP, CID_FOR_UNKNOWN_UNICODE on; DEHYPHENATE (16) and PRESERVE_IMAGES off |
| K7 | Zoo per-page signals (TOY, `c1_zoo.py`) | Repeated lines (threshold 3): "ACME Technical Report", "Page #" (3 pages each). Page: chars / images / ligatures / hyphen breaks / right→left jumps / ruled tables / NFKC delta = p.1 273/0/3/1/**4**/0/3 · p.2 74/0/0/0/0/**1**/0 · p.3 0/0/… (blank) · p.4 0/**1**/… (image-only) · p.5 101/0/0/0/0/0/0. p.1 line order: header, "Page 1", then L1 R1 L2 R2 L3 R3 L4 R4, then the ligature line. Jumps count body lines only (top and bottom 10% of the page excluded) |
| K8 | A two-column "paper" page drawn **column by column** (TOY, built in the script: title, 7 left lines, 7 right lines, an unruled 3 × 4 results table, a ligature line) | Default `get_text()`: true reading order (left column before right), **1** right→left jump (right column → table). `sort=True`: **3** lines hold words of both columns (e.g. "Dense retrieval maps each passage … Table 1 shows the …"). Line-end hyphens: `accu-/racy` (joined "accuracy" occurs elsewhere: R2 joins it) and `mar-/gin` ("margin" does not occur elsewhere: R2 leaves it). `find_tables()` default (ruling lines) 0; `strategy="text"` 1 "table" of 23 × 9 cells (it takes in the page's text, not just the table). The table comes out one cell per line: Method, NQ, TQA, SQuAD, BM25, 59.1, … 3 ligatures; NFKC changes 3 characters (+3); NFKC leaves `q·p` and `‖q‖ ≤ 1` alone but turns `x²` into `x2` and `10⁵` into `105`. 575 characters, 0 images. The table's numbers are made up |
| K9 | Corpus D per-page signals | chars per page: 2424, 2410, 2183, 2269, 2255, 2389, 2137, 2225, 2254, 2077, 2116, 2216, 2215, 2252, 2217, 2125, 2144, 2035, 2494, 2257, 2298, 2195, 2204, 2266, 2167, 2388, 2087, 2238, 2468, 2309, 2166, 2445, 636. Hyphen breaks on pages 8, 11, 12, 19 (1 each), 29 (2), 31 (1). Images 0 on every page; right→left jumps 0 on every page; ruled tables 0; ligatures 0; U+FFFD 0; `(cid:` 0 |
| K10 | Page-table arithmetic (TOY) | lengths 100, 50, 80 → rows (1, 0, 100), (2, 101, 151), (3, **152**, 232), total 232; a 4th page of 40 → row (4, 233, 273) added, rows 1–3 unchanged, total 273. Part F: rows (1, 0, 11), (2, 12, 23), (3, 24, 33); `page_of` 11 → (1, 11), 12 → (2, 0), 17 → (2, 5) (= S12) |
| K11 | Logged edits on the paper page (TOY) | R2 1 (accu-racy only), R3 3; 575 → 576 characters; `undo(apply(edits)) == raw`: True |
| K12 | Snapshot ids of the paper page (TOY; 06 §5.3 recipe, doc id `paper`) | cleaning `none` `202926ae0c7b` · `r3_ligatures_v1` `83b34428ba76` · `r2r3_v1` `63d18fdddf83` (text sha256[:12] `4033785d96eb`, `de3202cd0790`, `2fc9105c0b44`) |

**Corpus T numbers are not measured here.** The lesson quotes the research probe of 8 candidate arXiv papers (`study/research/phase_02_core_rag_baseline.md`, C1 §5.6, PyMuPDF 1.26.7, 2026-10-17; PDFs in the scratchpad only, deleted) as "research probe": line-end hyphens 15–323 per paper, ligatures 0–157, two-column pages 1–15, NFKC +108 characters on DPR and +160 on BERT, 1–4 right→left jumps per paper, RAPTOR's running header on every page. They become course facts only once DEC-3 freezes Corpus T and a script re-measures them.

## 2. Interface handed on (C2/C3)
`pages: list[Page(doc_id, page, text, parser)]`; `doc_text = "\n".join(...)`; page-table rows `{page, doc_char_start, doc_char_end, text_sha256}`; manifest `evaluation/snapshots/D_ea07572562ac.json`; text `evaluation/snapshots/ea07572562ac/climate.txt` (UTF-8, `"\n"`). The lab writes these only when the learner runs it; the tests wrote to the scratchpad.
