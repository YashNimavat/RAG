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
| Cause of the 37-character gap PyPDFLoader vs raw pypdf | **UNVERIFIED** |

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

## 2. Interface handed on (C2/C3)
`pages: list[Page(doc_id, page, text, parser)]`; `doc_text = "\n".join(...)`; page-table rows `{page, doc_char_start, doc_char_end, text_sha256}`; manifest `evaluation/snapshots/D_ea07572562ac.json`; text `evaluation/snapshots/ea07572562ac/climate.txt` (UTF-8, `"\n"`). The lab writes these only when the learner runs it; the tests wrote to the scratchpad.
