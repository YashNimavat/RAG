# I2 build spec: what each part of the I2 kit must contain

**What this is:** the brief shared by the lead (lesson HTML, gap audit, final checks) and the three helpers (verify notebook, apply-it tool, reading + questions) that built the I2 kit on 2026-10-18, following the P1/P2/P4 pipeline.
**What this is not:** the facts. Every number comes from [I2_FACTS.md](I2_FACTS.md) and `out_i2_measure.txt`; the mechanism is [i2_structure.py](i2_structure.py). Nothing here may contradict them.

## 0. Inputs every part reads

| Input | Use |
|---|---|
| `study/research/phase_04_indexing.md`, "Concept I2" (§1–§11) | content, gaps, blueprint, notebook plan (§7), tool plan and checklist (§8), quiz titles (§3) |
| `sources/verification/I2/I2_FACTS.md` + `out_i2_measure.txt` + `i2_lesson_data.json` | the only source of numbers |
| `sources/verification/I2/i2_structure.py` | the reference rules; the notebook and the tool re-implement them and must reproduce the facts exactly |
| `curriculum/WRITING_STYLE.md`, `study/PORTABLE_LESSON_STYLE.md` §B3 | house style |
| `study/FORMAT.md` | question and reading file formats |
| The P2 and P4 equivalents of each file | shape, length, conventions (copy the pattern, not the content) |

## 1. Decisions (lead, 2026-10-18)

- **Running example:** Corpus D, PyMuPDF 1.26.7 snapshot `ea07572562ac`. **Split level in the main path: L3 (section)**, cap C = 1,000 characters, no overlap inside a section; L2 and L4 (and L4 + merge, min 400) are the comparison arms. (Research §11 recommendation: section.)
- **Levels on D:** L1 title (24 pt), L2 chapter (18 pt), L3 section (13.56 pt), L4 sub-section (12 pt bold).
- **Rules** (from `i2_structure.py`): bold = `flags & 16` or `char_flags & 8`; body = most characters; levels by size rank, bold-at-body = next level; filters ≤ 12 words, no final `. ! ?`, not on ≥ 3 pages; join same-level lines of one block; align by cursor + `find`, fail closed; **a heading never ends a unit or a chunk (glue forward)**; balanced split n = ⌈ℓ/C⌉, cut at the sentence-ending line break within half a piece of each ideal point, else the nearest line break; merge adjacent units both < min-chars with the same parent and together ≤ C.
- **Retrieval:** MiniLM-L6 exact cosine; the 8 answerable seeds are `llm-draft` observations, never evaluation results. Budget = 4 × v0 mean chunk length = 3,432 characters. Verdict on 8 seeds: **inconclusive**, and the boundary bucket is empty (0 of 8).
- **Not built:** the LLMOps notebook (it needs `study/llmops/` first, as for P4). The lesson has a "planned" section.
- **Book pages:** not opened in this session. Cite them only as the research does, with "(per 04; not re-opened)" where the file format allows a note, and list them as UNVERIFIED in the lesson footer.
- **Never** use any item from `sources/coach/transfer_seed_bank.md`.
- No API call anywhere; no `.env` read.

## 2. File names (the study kit finds them by these patterns)

| Part | Path |
|---|---|
| Lesson | `study/lessons/I2_structure_chunking.html` + `I2_structure_chunking_gap_audit.md` |
| Verify notebook | `study/notebooks/I2_structure_chunking_verify.ipynb`, built by `sources/verification/I2/i2_build_verify_nb.py`, run by `i2_verify_nb_run.py` → `out_i2_verify_nb_run.txt` |
| Apply-it tool | `study/tools/structure_fit_check.py`; examples `study/tools/examples/climate_structure_report.md` (+ inspection sheet); tests `sources/verification/I2/i2_tool_test.py` → `out_i2_tool_test.txt`; `study/kit.py` `_TOOL_HINT["I2"] = "structure_fit"` |
| Reading + questions | `study/reading/I2_structure_chunking.md`, `study/questions/I2_questions.md`; checker `sources/verification/I2/i2_md_check.py` → `out_i2_md_check.txt` |

## 3. Lesson section ids (links from the reading file and questions may target these)

`#answer`, `#theory`, `#formulas`, `#s1` the failure · `#s2` inside the PDF (span dict, flags) · `#s3` body size · `#s4` headings: size vs size + bold · `#s5` error modes and repeated titles · `#s6` aligning to the snapshot · `#s7` section tree and breadcrumb · `#s8` split levels · `#s9` balanced split and merge · `#s10` continuation across pages · `#s11` invariants · `#s12` eye inspection · `#s13` measuring it · Full-only: `#f1` other structure sources · `#f2` frameworks · `#f3` tables and layout models · `#f4` what the studies say · then `#verify`, `#apply`, `#llmops`, `#check`, `#sources`.

## 4. Verify notebook (helper A)

Same shape as `study/notebooks/P4_embeddings_verify.ipynb` and its builder `sources/verification/P4/p4_build_verify_nb.py`: a setup cell with `check(label, got, expected, tol=0)`, then one section per lesson step with "What this verifies → code → check", Plotly charts, and a final summary cell printing the pass count.
- Sections follow research §7 items 1–9 and the lesson steps: S1–S14 of I2_FACTS. Every number in I2_FACTS §1 that the lesson uses gets a `check`.
- The notebook must be **self-contained** (re-implement the rules inline, not `import i2_structure`), since it lives in `study/`. The builder may test that its code gives the same chunks as `i2_structure.py`.
- PDF path: `RAG_PDF` environment variable, else the Windows default used by the P4 notebook, else `upstream/RAG_Techniques/data/…` relative search like P4's.
- Retrieval: use `sentence-transformers/all-MiniLM-L6-v2` from the local cache (`HF_HUB_OFFLINE=1`). If it is not cached, use the ONNX stand-in when `I2_MINILM_ONNX` points to a directory and `onnxruntime` imports; otherwise print `SKIPPED` for that section (count skips separately, never as passes).
- Charts (Plotly): the font-size ladder, the chunk-length histograms per arm, the page ruler for pp.1–2 (headings, page break, v0 chunks vs L3 chunks), CE@4 / CE@budget by arm.
- Must run top to bottom with 0 failures here (with the ONNX stand-in) and in under ~2 minutes; save outputs in the notebook.

## 5. Apply-it tool (helper B)

`structure_fit_check.py`: "Will structure-aware chunking work on my PDFs, and with what settings?" Pattern: `study/tools/embed_fit_check.py` and `qrels_check.py` (argparse, a Markdown report, a `--json` option, exit codes, a docstring with usage, no network).
- Inputs: `--pdf` (one or more), `--cap 1000`, `--split-level auto|1|2|3|4`, `--min-chars 400`, `--sample 10 --seed 0`, `--evalset` (M1/seed JSONL: report `straddles` and `crosses_page` per item against a per-page 1000/200 baseline), `--out report.md`, `--sheet inspection.md`.
- Outputs: research §8 (font histogram and body size; outline and tags; heading counts per level, size-only vs size + bold difference; column check from block x0; alignment rate; the outline print; chunk stats per split level; orphans and page cuts fixed; inspection sheet; the 11-check checklist S1–S11 with PASS/WARN/FAIL/MANUAL; the recommendation logic).
- `--split-level auto` = the deepest level whose median section ≥ min-chars (on D: L3, median 1,033.5).
- It must reproduce on D: body 12.0; 90 vs 282 headings; 1/21/68/192; 282/282 aligned; 11 repeated titles; 16 orphans and 8 cuts; L3 117 chunks (187/619/997), L2 86, L4 209, L4+merge 139; 0 invariant violations; the 10 inspection chunks 5, 33, 49, 51, 53, 62, 65, 97, 108, 113; seeds 0 straddling, 0 crossing.
- Tests (`i2_tool_test.py`, plain asserts or pytest-style functions run by `__main__`): the D numbers above; equality of chunks with `i2_structure.py` for L2/L3/L4/merge; a synthetic **zoo** of small PDFs made with PyMuPDF in a temp folder (bold body-size headings, a wrapped heading, a running header on every page, a two-column page, a PDF with an outline via `set_toc`, a page with no text layer, numbered headings, a bold lead-in phrase inside a paragraph line that ends with a full stop); CLI exit codes and bad-input errors.

## 6. Reading file and questions (helper C)

- Reading: FORMAT §3 shape (`<!-- kit:reading concept=I2 depth=short version=1 -->`), 1,800–3,000 words without code, book-first box (pages as listed in research §1, marked not re-opened), sections that mirror the lesson's Short path, "When not to use it", "Check yourself → `study/questions/I2_questions.md`".
- Questions: FORMAT §2 exactly. About 17–21 items: the research §3 titles (4 R, 4 A, 2 T), plus 1–2 pre-test items, extra R/A items so every lesson step s1–s13 is tested, and **one interview item** `set=interview source=AIQ-04-Q4` (verbatim question + notice; the repo's answer quoted as preamble, then our correction: the studies show no consistent winner, and "heading path fixes misses" is I5's claim). At most 2 external items in total.
- Every key point must be answerable from the lesson's **Short** mode and the reading file. Use only I2_FACTS numbers. Reread links point to reading-file anchors and `../lessons/I2_structure_chunking.html#sN`; there is no full `concepts/I2_*.md` lesson.
- `i2_md_check.py`: pattern `sources/verification/P4/p4_md_check.py`: links and anchors resolve (Markdown and the lesson's ids), page references well-formed, `quiz.py --check` passes, every number in the two files appears in I2_FACTS/out_i2_measure (or is a formula), no 15-word run shared with the AIQ answer except inside the quoted preamble, no coach-banned phrases, no hidden-seed wording.

## 7. Lead: lesson and checks

The lesson follows PORTABLE_LESSON_STYLE §B2 with the shell copied from `study/lessons/P4_embeddings.html` (style block, head script, top bar, contents panel, ↑ button, depth/theme/style scripts, `chart()` helper, quick-check engine), new sections per §3, inline SVG visuals from research §6 ("Visuals that earn their place"), and interactive parts: a heading-rule explorer (size only vs size + bold, per level counts), a split-level switcher (counts, histogram, a page ruler), a balanced-split calculator, and an invariant checker toy. Then: gap audit; browser tests (Playwright/Chromium, all themes, Short/Full, 390 px, no console errors); `quiz.py --check`; md check; tool tests; notebook run; kit route check; session log entry.
