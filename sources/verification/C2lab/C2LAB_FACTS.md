# C2LAB_FACTS: where every expected value in `labs/C2_chunking_lab.ipynb` comes from

Run date: **2026-10-08**. CPython 3.12.8, the project uv env (`rag_learning/.venv`), PyMuPDF **1.26.7**. Nothing was installed. There were no API calls and no network access, and `.env` was never read. Every value below came from a run. The output file is named in each row: `M` = `out_c2_measure.txt` and `B` = `out_c2_build_lab.txt`.

## 0. Files and how to re-run

| File | What it is | Saved output |
|---|---|---|
| `c2_setup.py` | The notebook's **given** setup cell, held as a string (single source). It loads the pages, recomputes `snapshot_id` and fails closed, and defines `PARAMS`, the inputs and the CHECK helpers (`_fp`, `_names`, `_spans`, `_limited`) | — |
| `c2_solution_ref.py` | **Reference solution** (throwaway, block format `# == <task>`). Never in the notebook | — |
| `c2_solution_alt.py` | An independent second solution in a different style, with some deliberately wrong *predictions* | `out_c2_labtest_alt.txt` |
| `c2_common.py` | Reads the solution blocks and runs setup + blocks in one namespace | — |
| `c2_measure.py` | All values, cross-checked against 07 H.1/H.3 (executed from the lesson text through `corrections/contracts_check.load_07_modules`) and against 06 §2.3/§5.3 | `out_c2_measure.txt` (ALL PASS; two runs byte-identical) |
| `c2_build_lab.py` | Writes the notebook. Computes each fingerprint by evaluating **the same expression** that the CHECK cell evaluates, on the reference | `out_c2_build_lab.txt` |
| `c2_lab_runner.py` | In-process runner (one namespace). Learner cells are taken from a solutions file (`-` = as shipped). It works in a temp dir, so the save cell never writes into WS | `out_c2_labtest_good.txt`, `_blank.txt`, `_alt.txt` |
| `c2_kernel_runner.py` | **Real Jupyter kernel** (project ipykernel via `jupyter_client`; nbconvert is not installed). Runs on a temp copy outside WS | `out_c2_labtest_kernel.txt` |
| `c2_variants.py` | 11 one-bug variants of the reference, each run through the lab | `out_c2_labtest_broken.txt` |

```bash
# from rag_learning/ (Git Bash); S = a scratch folder OUTSIDE the workspace
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1; V=sources/verification/C2lab
uv run python $V/c2_measure.py > $V/out_c2_measure.txt
uv run python $V/c2_build_lab.py labs/C2_chunking_lab.ipynb > $V/out_c2_build_lab.txt
uv run python $V/c2_lab_runner.py labs/C2_chunking_lab.ipynb $V/c2_solution_ref.py "$S/good" > $V/out_c2_labtest_good.txt
uv run python $V/c2_lab_runner.py labs/C2_chunking_lab.ipynb - "$S/blank" > $V/out_c2_labtest_blank.txt
uv run python $V/c2_lab_runner.py labs/C2_chunking_lab.ipynb $V/c2_solution_alt.py "$S/alt" > $V/out_c2_labtest_alt.txt
uv run python $V/c2_variants.py labs/C2_chunking_lab.ipynb "$S/variants" > $V/out_c2_labtest_broken.txt
uv run python $V/c2_kernel_runner.py labs/C2_chunking_lab.ipynb $V/c2_solution_ref.py "$S/kgood"   # also: '-' and a variant
```

## 1. Expected values, CHECK by CHECK

| CHECK | Expected (reference value) | Fingerprint (B) | Produced by | Agrees with 07 |
|---|---|---|---|---|
| Setup | 33 pages; 72,593 chars; `SNAPSHOT_ID = ea07572562ac`; page starts 0, 2425, 4836 … | — | M §M1 | 06 §5.3 values, exact |
| Task 1 | Format only (the prediction is graded in Task 2) | — | — | — |
| Task 2 | `(T,10,3)` → (0,10)(7,17)(14,23); `(T,8,4)` → (0,8)(4,12)(8,16)(12,20)(16,23) | `t2_a01` 2f63b3f925f499e9 | M §M2 | C2-A-01, exact |
| Task 2 | Window counts for L = 1…5S at (10,3)(8,4)(300,60)(7,6)(5,0) = D.2 formula; spans = 07 H.1 | `t2_counts` e8f28915561eb6ef | M §M2 (0 mismatches over 6 settings) | D.2 formula |
| Task 2 | `doc_text` fixed 1000/200 = **91** (shown in plain text) | — | M §M2: lengths 593 / 1000 / 1000 | 07 D.2: 91 on PyPDFLoader's 72,523 chars. Same count; the CHECK says so |
| Task 2 | ValueError for overlap == size, overlap > size, negative overlap, size 0; `""` → `[]` | — | M §M2 | 07 H.1 table |
| Task 3 | The learner's `check_chunks` passes good lists and catches 7 broken lists (built from explicit spans (0,12)(8,20)(16,23), independent of Task 2) | — | `out_c2_labtest_*` | H.1 properties |
| Task 4 | Part F containment: 300/0 → `[]`, 300/60 → `[2]`; T (10,3): [6,9) → [0], [8,10) → [0,1] | `t4_contain` 4e38ecbfa1c6a65b | M §M3, B | Part F, exact |
| Task 4 | `p_formula` at 3 dp: 0.501, 0.626, 0.835, 1.0, 1.0, 0.999, 0.939, 0.958 | `t4_formula` f7f5921faaabfecc | M §M3 | D.3 table (0.501/0.626/0.835; 0.99875, 0.93875) and Part F 0.958 |
| Task 4 | `p_brute(20000, 1000, O, 500)` at 4 dp: 0.5138, 0.6320, 0.8375 | `t4_brute` be663923c3c94f59 | M §M3 | D.3 last column, exact |
| Task 4 | Guarantee threshold: `p_brute(20000,1000,200,201) == 1.0`, F = 202 → 0.99879 < 1 | — | M §M3 | D.3 "F ≤ O + 1 = 201" |
| Task 5 | `split_spans(W,0,22,SEP,10)` = (0,4)(4,8)(8,12)(12,15)(15,19)(19,22) | `t5_pieces` adfc239e8ecda1ab | M §M4 | C2-A-03 pieces |
| Task 5 | `recursive_chunks(W,10,4)` = (0,8)(4,12)(8,15)(12,22) | `t5_w` 41951b95c262de52 | M §M4 | C2-A-03 result |
| Task 5 | `recursive_chunks(PARA,300,60)` = [0,294)[238,534)[478,773)[714,785); fact in chunk 2 | `t5_para` b00e3a1585888285 | M §M4 | Part F step 3, exact |
| Task 5 | `"short "+"x"*25+" tail"` at 10/0 → (0,10)(10,20)(20,30)(30,36) (the `""` fallback) | `t5_long` 2d65277e77e6bbe4 | M §M4 (= 07 H.1) | H.1 behaviour. 07 D.4's 9/10/6 pieces are LangChain's (separator at the start, stripped) |
| Task 5 | 200 random texts: `check_chunks` passes; real overlap ≤ overlap (characters); `doc_text` 1000/200 = **92** | — | M §M4: 300 random settings identical to 07 H.1 | 07 H.1: 92 (PyPDFLoader); same |
| Task 6 | Per-page spans: **97** chunks; none crosses a page; round-trip; = `recursive_chunks(page)` shifted | `t6_all` 9d9ebc33b1c487e3 | M §M5 (= 07 H.3 `chunk_document(per_page)` spans) | 07 D.8: 97 (PyPDFLoader); same count |
| Task 6 | Toy `["abc def", "", "ghi jk"]` at 4/1 → (0,4,1)(4,7,1)(9,13,3)(13,15,3) | `t6_toy` daa87c5c21be3a1b | B | — |
| Task 6 text | Whole joined text: 92 chunks, **41** cross a page | — | M §M4 | 07 D.8 says **39** on PyPDFLoader text. **Differs; the task text says so** |
| Task 6 print | Lengths 393 / 935 / 1000 | — | M §M5 | 07 D.8: 391 / 933 / 999 (PyPDFLoader). **Differs; the print says so** |
| Task 7 | `params_hash(PARAMS)` = **1ca9c5a3b548** | `t7_ph` 05434e71a00f90df | M §M6 | — (06 fixes no recipe; see §2) |
| Task 7 | 97 records; keys = 06 §2.3 `Chunk` fields (parsed by `ast`); round-trip; 1 segment each, page-relative, inside its page; `text_sha256`; ids `climate:ea07572562ac:1ca9c5a3b548:00000…00096`; deterministic; overlap 199 → all-new ids | `t7_records` a453b7b419d9134e | M §M6 (spans, text, sha256 = 07 H.3 DocChunks; segments = 07 H.3 `to_page_segments`) | — |
| Task 8 | 64 same-page pairs; real overlap min / median / max 109 / 177 / 200; exactly 200: 2; first four 182, 142, 199, 179 | `t8_ao` 3a64eef6bfe6cfd7 | M §M7, B | 07 H.2: 180, 140, 197, 177 (LangChain + PyPDFLoader, whitespace stripped). **Differs; the CHECK print says so** |
| Save | `chunks.jsonl`: 97 lines, 122,774 bytes, sha256 `d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b` | — | M §M6, B | — |

Rounding guard (M §M3): no fingerprinted value lies within 1e-6 of its rounding boundary. Formula values are fingerprinted at 3 dp because 501/800 = 0.62625 sits exactly on a 4-dp boundary.

## 2. Interface assumptions and 07 ↔ 06 mismatches (06 wins)

| # | 06 says | 07 H.1/H.3 says | The lab does |
|---|---|---|---|
| 1 | separators `["\n\n", "\n", " ", ""]` | `("\n\n", "\n", " ")`; single characters only as an implicit fallback | `""` means single characters. Feeding `""` to H.1's `_split_spans` literally would never advance (`'abc'.find('', 1, 3) == 1`, M §M4). Spans are identical to H.1 (corpus + 300 random settings, M §M4) |
| 2 | `chunking.name: recursive_char` | `ChunkerConfig(name="recursive")` | `chunker = "recursive_char"` |
| 3 | config keys `chunk_size`, `chunk_overlap` (§2.4) | `size`, `overlap` | `PARAMS` = the 06 §2.4 `chunking:` block verbatim |
| 4 | "params hash" (no recipe) | `sha256(json.dumps(asdict(cfg), sort_keys=True))[:12]` | **Interface assumption:** the same recipe over the 06 block → `1ca9c5a3b548`. The same spans under 07's dict give `77bc4c45809b` (3 separators; the id used in contracts_check), `12eafa2247a1` (+ `""`), `0ad9b961bc23` (`recursive_char` + `""`); fixed 1000/200 gives `db1d77b74d1f` (M §M6) |
| 5 | `Chunk` dataclass with `page_segments: tuple[PageSegment]` and `meta` | `DocChunk` (no `meta`) | **Interface assumption:** JSON-ready dicts; `page_segments` = a list of `{"page","char_start","char_end"}`; `meta = {}`. Field names and order = 06 §2.3 (checked by `ast`) |
| 6 | `Chunk` = the record | H.1 `Chunk(chunk_id:int, text, char_start, char_end, page_start, page_end)` = a working type | The lab's `Chunk` is H.1's working type without `page_start`/`page_end` (the page-aware chunker is not in this lab); records are dicts |
| 7 | "Recursive character splitter" | H.1: no whitespace stripping | No stripping (offsets exact). LangChain strips, so its boundaries differ (07 Part F) |
| 8 | PyMuPDF text (72,593 chars) | 07's corpus numbers come from PyPDFLoader (72,523) | Counts are equal (91, 92, 97). The page-crossing count (41 vs 39), the lengths and the overlaps differ, and the task text states each difference |

**Interlock note for the other helpers (not edited by me):** `sources/verification/C3/c3_measure.py` builds its records with 07's `ChunkerConfig` field names and a **fixed-window** given chunker (`chunker="fixed"`, params_hash `db1d77b74d1f`, out_c3_measure.txt line 10). The record fields match this lab's, but the ids do not. If C3 is to consume C2's v0 output, one `params_hash` input must be chosen for the whole course: either the 06 block (this lab: `1ca9c5a3b548`) or 07's `ChunkerConfig` with 06 values (`12eafa2247a1`/`0ad9b961bc23`).

## 3. Test results

| Run | Result |
|---|---|
| Reference, in-process | **9/9 CHECK pass** |
| Reference, **real kernel** (jupyter_client, temp copy outside WS) | **9/9 pass**; the save cell wrote `C2_out/ea07572562ac_1ca9c5a3b548/chunks.jsonl` in the temp dir |
| Independent alternative solution (`c2_solution_alt.py`) | **9/9 pass**; its wrong predictions are reported (Task 1 "not right"; Task 4 predicted [1]/200; Task 6 predicted 92; Task 8 predicted True), not blocked |
| Blank notebook, in-process and real kernel | **0/9** |
| 11 one-bug variants | **11/11 fail their intended CHECK**: off-by-one stride → Task 2 (+4); overlap counted in pieces, not characters → Task 5 (+6, 7, 8, save); chunk crosses a page → Task 6 (+7, 8, save); uuid ids → Task 7; params_hash via builtin `hash()` → Task 7; page-relative offsets (C2-A-05) → Task 6; weak `check_chunks` → Task 3; no validation and no stop (C2-A-04) → Task 2 via `TimeoutError` (also in a real kernel); find-loop on `""` → Task 5 via `TimeoutError`; whitespace stripping → Task 5; page-relative record offsets → Task 7 |
| Acceptance suite after this work | 145/145 (unchanged; nothing it reads was edited) |

A full in-process run of the reference took about 0.6 s.

## 4. UNVERIFIED / not done

- **VS Code's notebook UI** was not opened. Rendering there is UNVERIFIED; execution was checked in a real ipykernel.
- `_limited` relies on `sys.settrace`. Inside the **VS Code debugger** it would replace the debugger's tracer during those calls (restored afterwards). This is UNVERIFIED under the debugger; normal "Run cell" is fine.
- `labs/C2_out/` is created only when the learner runs the save cell. I did not check whether `.gitignore` covers it, and I did not touch `.gitignore`.
- Whether C3 will read `chunks.jsonl` as written depends on the C3 helper (see the interlock note).
- 07 D.8's other PyPDFLoader facts (8 mid-sentence cuts, 16 orphaned headings, the PPP sentence in 0 of 97) were **not** re-measured on PyMuPDF text and are not used in the lab.
