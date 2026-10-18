# I2_FACTS — what the I2 lesson can rely on (run-verified)

Run date: **2026-10-18**, in a Claude Code cloud session (Linux), not on Yash's machine. Every number in the I2 lesson, reading file, question file, verify notebook and tool example is listed here with the section that produced it. Numbers not produced by these runs are marked CITED, DERIVED or UNVERIFIED (§2).

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.3 (Linux), the project uv environment (`uv sync`, same lock file as Yash's machine).
- **Versions.** pymupdf 1.26.7 · numpy 2.5.3 · tokenizers 0.23.2. For S14 only: `onnxruntime` (ephemeral, `uv run --with onnxruntime`; **not added to the project**).
- **Corpus D.** `Understanding_Climate_Change.pdf` from `NirDiamant/RAG_Techniques` at `009adba`, downloaded from raw.githubusercontent.com: sha256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669`, 206,372 bytes, 33 pages (= the 06 §5.3 lock). Snapshot: PyMuPDF 1.26.7 `page.get_text()`, pages joined with `"\n"`; doc_text 72,593 characters, sha256 `5106772efa77…`, **snapshot_id `ea07572562ac`** (the 06 §5.3 recipe, recomputed in S1; = 06).
- **The MiniLM stand-in (S14 only).** Hugging Face is blocked in the cloud container, so `sentence-transformers/all-MiniLM-L6-v2` could not load. S14 uses the public **ONNX export** of the same model (`chroma-onnx-models` `all-MiniLM-L6-v2/onnx.tar.gz`, sha256 `913d7300…`; its `config.json` names `sentence-transformers/all-MiniLM-L6-v2`), run with `i2_onnx_embed.py`: WordPiece tokenizer, 256-token truncation, mean pooling, L2 normalisation (the L6 pipeline in P4 K1). **Cross-check:** on v0's 97 chunks it reproduces P4 K3 exactly (D-002 top-5 69, 68, 27, 17, 84; cosines 0.4606, 0.4513, 0.4386, 0.4385, 0.3387) and P4 K4 exactly (first-hit ranks [3, 3, 1, 1, 1, 1, 2, 2], MRR@10 0.708). The verify notebook re-runs S14 with sentence-transformers on Yash's machine.
- **Not available here:** the book PDFs (no page was opened; every book page in the lesson is "per 04/02, not re-opened", as in the research file), and the tiktoken encodings (blocked), so **no cl100k/o200k token counts** are new here; token sizes use MiniLM's WordPiece tokenizer.
- **No API calls.** No Groq, Cohere or Claude call; `.env` is never read.
- **Scripts and outputs** (this folder):

  | File | What it is |
  |---|---|
  | `i2_structure.py` | The reference mechanism: span records, body size, heading rules, alignment, section tree, units, balanced split, merge, page segments, invariants |
  | `i2_measure.py` → `out_i2_measure.txt` (stderr empty) | S1–S15, and `i2_lesson_data.json` (the lesson's chart data) |
  | `i2_onnx_embed.py` | The ONNX MiniLM stand-in used by S14 |
  | `i2_sources.py` → `out_i2_sources.txt` | Repo cells and lines at `009adba`, README absence checks, the AIQ Q4/Q13/Q14 text and licence: **ALL PASS** |

- **Re-run** (from `rag_learning/`):
  ```bash
  PDF="C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/I2/i2_measure.py "$PDF" > sources/verification/I2/out_i2_measure.txt
  # S14 retrieval with the ONNX stand-in (optional):  uv run --with onnxruntime python ... "$PDF" <onnx dir>
  ```
- **Determinism.** Two consecutive runs gave **byte-identical** stdout (`cmp`).

## 1. Facts by section (`M` = `i2_measure.py`, section in `out_i2_measure.txt`)

### S1 Snapshot and document structure sources

| Fact | Value |
|---|---|
| Pages / doc_text characters / snapshot_id | 33 / 72,593 / `ea07572562ac` |
| `doc.get_toc()` | `[]` (no outline) |
| Catalog | `StructTreeRoot` present (tagged PDF); `MarkInfo <</Marked true>>` |
| Creator | Microsoft® Word 2021 |

### S2 One real span (page 1)

| Fact | Value |
|---|---|
| Span keys | alpha, ascender, bbox, bidi, char_flags, color, descender, flags, font, origin, size (+ text) |
| Title span | `'Understanding Climate Change '`, size 24.00, **flags 20** (= 16 bold + 4 serif), char_flags 24, `TimesNewRomanPS-BoldMT`, bbox (72.0, 73.1, 403.4, 99.6) |
| Chapter span | `'Chapter 1: Introduction to Climate Change '`, size 18.00, flags 20 |
| Body span | size 12.00, **flags 4** (serif only), char_flags 16, `TimesNewRomanPSMT` |

### S3 Font sizes, weighted by characters

| Size, bold? | Characters | Share |
|---|---|---|
| 24, bold | 28 | 0.0% |
| 18, bold | 855 | 1.2% |
| 13.56, bold | 1,666 | 2.4% |
| 12, bold | 4,057 | 5.8% |
| **12, regular** | **63,762** | **90.6%** |
| 11.04, regular (Calibri) | 0 (blank) | 0.0% |

Body size **12.0**. Spans per size: 12.0 → 1,006 · 13.56 → 68 · 18.0 → 22 · 24.0 → 1.

### S4 Heading detection

| Fact | Value |
|---|---|
| Text lines / all-bold lines / bold lines with more than one span | 1,097 / 283 / **0** |
| Size only | **90** headings: L1 1, L2 21, L3 68 |
| Size + bold at body size | **282** headings: L1 1, L2 21, L3 68, **L4 192** |
| Missed by size only | **192 of 282 (68.1%)** |
| Joined wrap | 1: p.7 "Chapter 5: The Role of Technology in Climate Change" + "Mitigation" (22 level-2 lines → 21 headings) |
| Hyphen headings | 15 (e.g. "Public-Private Partnerships" p.12, "Nature-Based Solutions" p.14 and p.26); **each is one span** (the research's three-run worry does not occur in PyMuPDF) |
| Removed by the filters (> 12 words, final . ! ?) / running headers (≥ 3 pages) | 0 / none |

### S5 Same text, same order

`dict` lines, each + `"\n"`, rebuild `page.get_text()` **exactly on 33 of 33 pages**. This is what lets a heading line be found in the snapshot.

### S6 Alignment

| Fact | Value |
|---|---|
| Aligned | **282 of 282**; every heading lies on its own page |
| "Coal" | L4, page 1, doc [2418, 2423); page 1's text ends at 2424; next text `'\n\nCoal is the most carbon-intensive…'` |
| First headings | L1 "Understanding Climate Change" @0 · L2 "Chapter 1…" @30 · L3 "Historical Context" @467 · L3 "Modern Observations" @1072 · L2 "Chapter 2…" @1621 · L3 "Greenhouse Gases" @1658 |

### S7 Tree and repeated titles

**11 repeated titles** (22 headings): Carbon Capture and Utilization (p.8 L3, p.23 L3) · Carbon Utilization (p.8, p.23, both L4) · International Agreements (p.6 L4, p.23 L3) · International Collaboration (p.10 L3, p.16 L4) · Marine Ecosystems (p.5, p.13) · Nature-Based Solutions (p.14 L4, p.26 L3) · **Paris Agreement (p.10: Ch6 > International Collaboration; p.23: Ch16 > International Agreements)** · Policy and Governance (p.12 L3, p.18 L4) · Research and Innovation (p.7 L3, p.16 L4) · Smart Grids (p.8, p.22) · Youth Engagement (p.13, p.32).

Chapter 6 tree (characters from the heading to the next heading of the same or higher level):

```
L2 Chapter 6: Global and Local Climate Action           2728  p.10
  L3 International Collaboration                          695  p.10
    L4 United Nations Framework Convention … (UNFCCC)     348
    L4 Paris Agreement                                    318
  L3 National Strategies                                  913
    L4 Carbon Pricing 290 · Renewable Energy Targets 295 · Emission Reduction Regulations 307
  L3 Local and Community Initiatives                     1076
    L4 Urban Climate Action 362 · Community-Based Conservation 346 · Education and Awareness 335 (p.11)
```

Section lengths: L2 21 sections, 1,591 / 3,336 / 6,058 (min/median/max), mean 3,455.4 · **L3 68 sections, 549 / 1,033.5 / 1,898, mean 1,041.3** · L4 192 sections, 243 / 334 / 636, mean 336.5.

### S8 Page-break failures on PyMuPDF text (closes I2-E7)

- **16 orphaned headings** (page ends in a detected heading): 1→2, 2→3, 3→4, 4→5, 5→6, 6→7, 7→8, 8→9, 10→11, 11→12, 17→18, 18→19, 20→21, 27→28, 30→31, 31→32. **Same pages as LAB_FACTS §7** (PyPDFLoader).
- **8 mid-sentence cuts**: 12→13, 14→15, 15→16, 16→17, 21→22, 22→23, 24→25, 28→29. Same as LAB_FACTS §7.
- 24 of 32 page breaks do not end in `. ! ? :` or a quote (= LAB_FACTS).

### S9 Chunk arms (cap C = 1,000 characters; structure arms have no overlap)

| Arm | Chunks | Length min / median / max | Mean | Chunks on 2 pages | Histogram, 100-char bins (0–99 … 900–1000) |
|---|---|---|---|---|---|
| v0 per-page recursive 1000/200 | 97 | 393 / 935 / 1000 | 857.9 | 0 | 0,0,0,1,0,9,13,5,3,66 |
| Cross-page recursive 1000/200 (the control) | 92 | 755 / 962.5 / 999 | 954.8 | 41 | 0,0,0,0,0,0,0,1,1,90 |
| Structure, split at L2 (chapter) | 86 | 644 / 843.5 / 1000 | 844.1 | 29 | 0,0,0,0,0,0,9,27,17,33 |
| **Structure, split at L3 (section)** | **117** | **187 / 619 / 997** | **620.5** | **27** | 0,1,0,18,16,18,29,15,6,14 |
| Structure, split at L4 (sub-section) | 209 | 187 / 338 / 636 | 347.3 | 24 | 0,1,40,143,19,2,4,0,0,0 |
| Structure, L4 + merge (min 400) | 139 | 187 / 545 / 772 | 522.3 | 25 | 0,1,7,36,19,17,34,25,0,0 |
| Structure, L3, **size-only** headings | 117 | 187 / 619 / 997 | 620.5 | 27 | identical chunks to the L3 arm |

- L3: 25 sections give 1 chunk, the other 46 give 2 (sections over the cap: 46 of 71 units).
- L4 + merge: 70 chunks are merged.
- **At L3 the size-only detector gives exactly the same 117 chunks.** The 192 bold sub-headings change nothing at section level; they matter for splitting at L4 and for the breadcrumb.
- L3 split units: 71 (68 sections + 3 chapter openings with text before their first section). Min 187.

### S10 Balanced split

- Shortest L3 section over the cap: Ch11 > Advocacy and Activism, **1,004 characters**. n = ⌈1004/1000⌉ = 2, ideal 502 each. The cut goes to the sentence-ending line break nearest 502 (within half a piece): pieces **341 + 663**. Naive cap cutting: 1,000 + **4**.
- Longest L3 section: Ch2 > Greenhouse Gases, 1,935 characters → **990 + 945**.

### S11 Invariants (all structure arms)

Round trip `doc_text[a:b] == text`, cap, gaps (non-whitespace text not in any chunk), crossing (a split-level boundary inside a chunk, other than a glued heading run), page segments rebuild `[a, b)`: **0 violations in every structure arm**. L3 chunks tile the document: no overlap, gaps only whitespace.

### S12 Containment demos

| Demo | v0 | Cross-page control | L2 | L3 | L4 | L4+merge |
|---|---|---|---|---|---|---|
| "Coal" heading + its first body line in one chunk | **no** | — | — | **yes** (chunk 3, pages 1–2) | — | — |
| Whole PPP sentence (doc [26866, 26997), pp.12→13) in one chunk | **no** | yes | yes | **yes** (path Ch8 > Policy and Governance) | yes (… > Public-Private Partnerships) | yes |

PPP sentence: `'Public-\nprivate partnerships (PPPs) can leverage resources, expertise, and innovation to implement \n\nlarge-scale climate solutions.'`

### S13 Eye inspection: 10 random L3 chunks (`random.Random(0).sample`)

Chunks 5, 33, 49, 51, 53, 62, 65, 97, 108, 113. **10 of 10 start at a heading and end at a sentence end** (65 and 108 are second pieces that start at a sub-heading). Pages: 51 (15–16), 62 (18–19), 97 (27–28) and 108 (30–31) run across a page break. Paths are correct by eye (the tutor's reading in this session; Yash's own verdict sheet is the notebook's task).

### S14 Seeds and retrieval (MiniLM-L6 via the ONNX stand-in; 8 answerable `llm-draft` seeds: **observations, never evaluation results**)

- 11 of the 12 single-segment seed quotes match the snapshot text exactly; the 12th, D-007's first quote, is shorter than its span (it stops at "such as the"). Straddling uses research §5's rule: an alternative counts as held only when one chunk contains all of it.
- **Buckets: `straddles_v0` = 0 of 8, `crosses_page` = 0 of 8.** No seed tests the failure I2 fixes. D-005, D-006, D-007 have 2 evidence groups.
- Equal budget = 4 × v0's mean chunk length = **3,432 characters**, packed in rank order until the next chunk would not fit.

| Arm | CE@4 | CE@budget | CE rank (D-001…D-008) | MRR@10 by CE | First-hit ranks | MRR@10 first hit | WordPiece max (> 256) |
|---|---|---|---|---|---|---|---|
| v0 | 8/8 | 8/8 | 3,3,1,1,1,1,3,2 | 0.688 | 3,3,1,1,1,1,2,2 | **0.708** (= P4 K4) | 182 (0) |
| Cross-page control | 7/8 | 6/8 | 4,3,2,1,1,1,5,2 | 0.598 | 4,3,2,1,1,1,4,2 | 0.604 | 196 (0) |
| L2 chapter | 8/8 | 8/8 | 2,3,1,1,2,1,4,1 | 0.698 | 2,3,1,1,1,1,2,1 | 0.792 | 175 (0) |
| **L3 section** | **8/8** | **7/8** | 2,3,1,1,4,3,4,2 | 0.521 | 2,3,1,1,1,3,3,2 | 0.625 | 196 (0) |
| L4 sub-section | 7/8 | 8/8 | 1,1,1,1,2,1,5,1 | 0.838 | 1,1,1,1,1,1,3,1 | **0.917** | 118 (0) |
| L4 + merge 400 | 7/8 | 8/8 | 1,1,1,1,4,3,5,2 | 0.660 | 1,1,1,1,1,3,3,2 | 0.771 | 140 (0) |
| L3 size-only | 8/8 | 7/8 | = L3 | 0.521 | = L3 | 0.625 | 196 (0) |

- **What changes, and why.** The L4 arm ranks the single-fact seeds best (D-001, D-002, D-003 at rank 1) because its chunks are small and focused, but it misses D-007 at k = 4: small chunks need more slots for a two-fact question. At an equal budget it recovers (8/8). L3 is no better than v0 on these 8 seeds.
- **What this does not show.** With 8 draft seeds, none of them straddling a v0 boundary or a page, the bucket I2 targets is empty. The honest verdict is **inconclusive**; the experiment needs `straddles_champion` and `crosses_page` items (research §6, E3).
- No chunk in any arm is over MiniLM's 256 WordPiece tokens.

## 2. CITED, DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| Book pages Ch7 p.1–2/11, Ch7 p.8/11, Ch9 p.10–11/14, Ch14 p.4–5/13 | **UNVERIFIED in this session** (book not present); per 07, 04 and 02, as in the research file. Yash's local pass must open them |
| PyMuPDF flag bit values and `get_toc()` behaviour (source lines) | CITED: research [I2-S1], read from PyMuPDF 1.26.7 source; S2 and S1 agree on Corpus D |
| `pymupdf4llm` 0.2.9 `IdentifyHeaders` is size-only and would give `#`/`##`/`###` and miss the 192 | CITED from source [I2-S2]; **not run** (not installed). S4's "size" rule is the same idea |
| LangChain `MarkdownHeaderTextSplitter` strips lines, joins with `"  \n"`, no offsets, no cap | CITED [I2-S3]; not installed, not run |
| unstructured `chunk_by_title` defaults (500/500/500), docling `HybridChunker` defaults | CITED [I2-S4, S5]; read-only |
| Element-type chunking (FinanceBench), NVIDIA page-level 0.648, Shaukat et al. nDCG@5 0.459, editorial-content result, financial PDF MRR 0.655, Snowflake 5–10% | **UNVERIFIED** (search-checked only, research [I2-S7–S13]) |
| The `[P]` thresholds: 12 words, 3 pages, min-chars 400, cap 1,000 | [P] = project choices, not measured optima |
| CE@k, Span-Coverage and gold groups (06 §7.2–§7.3) | CITED: 06; P6 D.7 |

## 3. Notes for 02, 03, 04 and 06 (not edited; recorded here)

- Research I2-E7 is **closed**: the 16 orphans and 8 cuts re-measure identically on PyMuPDF text (S8).
- Research §1's "hyphen headings may be three runs" does not hold in PyMuPDF 1.26.7: all 15 are one span (S4).
- Research §6 step 9's "1,068-character section" does not exist at L3 under these rules; the real shortest over-cap section is 1,004 characters (S10).
- The seeds give `straddles_v0` = 0 and `crosses_page` = 0 (S14): the boundary bucket in 02/06 is empty on today's eval set. M1 must add such items before v1.1 is measured.
- The cross-page control (92 chunks, 41 of them on two pages) matches LAB_FACTS §7's 92 / 39 only in count; the page-crossing count differs because LAB_FACTS used PyPDFLoader text (and possibly a different "crosses" test). Not settled here.
