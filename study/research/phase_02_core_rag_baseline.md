# Phase 2 research: Core RAG baseline → v0

**What this is:** the research and gap audit for Phase 2 (C1 parsing, C2 chunking, C3 embedding and indexing, C4 dense retrieval, C5 generation with citations, C6 the v0 pipeline, C7 structured-data RAG), done 2026-10-17 and 2026-10-18 by Claude (Opus 5.5).
**What this is not:** lessons or code. Nothing in the course was changed, nothing was installed, and no Groq, Cohere, Claude or LangSmith call was made.

**How it was done.** One research helper per concept followed `RESEARCH_PROMPT.md` §2–§7 and applied `LLMOPS_FOUNDATION.md` (cited here as "Foundation §x"). Each helper opened the book pages and repo cells it cites, read the existing course files, and checked outside sources. A few local, offline measurements were made with the installed PyMuPDF and tokenizers, for example C2's chunk counts and C1's probe of candidate Corpus T papers. Book text was extracted only into the session scratchpad and deleted afterwards. Facts that could not be checked are labelled **UNVERIFIED**. All web facts are external and dated 2026-10-17.

**How to read it.** Read the Summary first. Each concept then has the same 11 parts as the template. Error ids such as `E-C3-1` are local to their concept. Source ids such as `[C4-1]` are listed under each concept's §1 and again in the Sources list at the end.

---

## Summary (read this first)

**The 5 most important gaps across the phase**
1. **The prerequisites are not studied, so every Phase 2 lesson must carry its own bridges.** P1, P4, P5, P6 and P7 are all `not_started`, and four open mix-ups land here: MC-001 (tokens vs characters) in C2, MC-002 and MC-005 (query embedding, the k trade-off) in C4, and MC-003 (prompt building vs overlap) in C5. Short mode has to teach cosine and normalisation, exact top-k, Hit@k and CE@k, the overlap unit, and index time vs query time where they are first used. The C7 lesson also needs pandas and SQL basics, which no part of the course teaches.
2. **The lab code paths break the caching rule (D-32) and use stale API fields.**
   - The C5 lab's Task 9 and the C6 gate run (Task 12) call Groq and Cohere directly, with no cache and no replay.
   - Both still send the deprecated `max_tokens` instead of `max_completion_tokens`.
   - Foundation error E2 is live in the C3 lab: the Cohere call, `embed_hash` and the cache key leave out `output_dimension`, `embedding_types` and `truncate`.
3. **The v0 trace schema is out of date in three places** (lesson, lab check, example trace). `finish_reason`, `reasoning_effort`, `max_tokens` and the Foundation E4 fields are missing, so a real Groq run would pass the lab while failing 06 §2.5. C5's answer record and C6's trace must become **one** shared schema.
4. **Corpus T is not chosen, and the evidence from Corpus D does not carry over to it.**
   - DEC-3 blocks Gate 2→3 and approval gate B.
   - A probe of 8 candidate arXiv papers found different artifacts from Corpus D: 15–323 line-end hyphens per paper, ligatures, and mostly column-by-column reading order.
   - NFKC normalisation would shift character offsets by 108 (DPR) to 160 (BERT) characters.
   - So the cleaning rules for T must be decided **before** M1 labels any gold spans.
5. **The default embedder's facts are unconfirmed, and the course has measured only the fallback.**
   - Every measured retrieval and truncation number is from local MiniLM, not from Cohere `embed-v4.0`.
   - The input limit conflicts: the Models API says 8,192 tokens, the docs say 128k.
   - Whether the vectors come back unit length, the price and the size of the `input_type` effect are **UNVERIFIED**.
   - 06 §3.2 has no row for `embed-v4.0` at all.
   - About 15 recorded Cohere calls (C3: 11, C4: 4) would settle all of these.

**Tools to add across the phase** (none installed; details in each concept's §10)
- The Foundation's framework set (`langchain-core`, `langchain-text-splitters`, `langgraph`, `langsmith`, `arize-phoenix-otel` plus instrumentors): needed by every Phase 2 LLMOps notebook. No `langchain-groq` or `langchain-cohere` (they conflict with the pinned SDKs).
- `pdfplumber==0.11.10` and `pypdf==6.19.0` (C1): a second-parser comparison arm, and parity with the repo's `PyPDFLoader`. Both are light and permissively licensed. PyMuPDF 1.26.7 stays the pinned parser.
- `langchain-community==0.4.2` (C1, LLMOps notebook only): to show the loaders' hidden defaults (0-based page numbers, per-page `.strip()`).
- Optional: `pymupdf4llm==0.2.9` (C1; the last version that works with the 1.26.7 pin), Docling via `uvx` outside the lock (C1; a layout-model arm), `hypothesis` (C2; property tests), `duckdb` (C7; Full mode only). None is required.
- The **`study/llmops/` helper package** from Foundation §10 is not a library, but it is the real blocker. The LLMOps notebooks for C3–C7 cannot run until it exists.
- Seven new course tools, one per concept (each concept's §8): `parse_quality_check`, `chunk_fit_check`, `index_integrity_check`, a retrieval-diagnosis check, `citation_check`, a v0 health check, and a question-routing check for tables.

**Decisions Yash must make** (at most 5, each answerable in a word; the per-concept preference questions are in each §11)
1. **Corpus T files:** set **a**, set **b**, or a **mix** of the eight probed candidates (C1 §5.6)? This unblocks Gate 2→3.
2. **One `params_hash` recipe for the whole course**, built from the 06 `chunking:` block? **Yes** is recommended (C2 §4 and C3 currently disagree).
3. **Record the Cohere verify calls** (about 15 calls, once) as soon as the helper package exists? **Yes** is recommended. They settle the 8,192 vs 128k limit, unit length and the `input_type` effect.
4. **Apply-it tools on your own documents:** **local** only by default, or allow external API calls? **Local** is recommended. No text from your own documents leaves the machine unless you opt in.
5. **First Claude arm** when credits exist: **Haiku** or **Sonnet**? **Haiku** is recommended, with a Citations-API variant (C5).

**Size of the build work**

| Concept | Size | Why |
|---|---|---|
| C1 parsing | M | The lesson exists (698 lines) but predates the house style; 4 new parts (Unicode/NFKC, reading order on real papers, the parser landscape, measuring parse quality). The apply-it tool is new and the largest piece |
| C2 chunking | M | 07 is complete and lab-checked, so this is a rewrite into the Short/Full format plus 4 additions (overlap unit, offsets by search, the Cohere limit, an evidence table). New verify notebook, `chunk_fit_check.py`, about 17 questions |
| C3 indexing | M | A strong, measured lesson to reshape, plus 4 short sections (truncation, the new key fields, model identity, storage). The integrity tool has 12 checks; the verify notebook records 11 Cohere calls |
| C4 dense retrieval | M | A rewrite plus 5 bridges and 2 new sections (exact terms; the framework box). The tool can reuse the `bm25_fit_check.py` skeleton |
| C5 generation | M | A rewrite with 4 bridges and about 9 gap fixes. `citation_check.py` makes no API calls. The LLMOps notebook depends on the helper package |
| C6 v0 pipeline | M | A rewrite with 6 visuals. The verify notebook mostly re-runs existing scripts. The health check is built from existing functions. It owns the first real Groq recording pass |
| C7 structured data | M | Nothing exists yet: lesson, questions, verify notebook, a 13-check tool and a LangGraph notebook with a 25-item golden set. The lesson itself is small (one CSV, 12 ideas) |
| Prerequisite: `study/llmops/` | M | Foundation §10. Blocks the LLMOps notebooks for C3–C7 and the C6 gate run |

**API calls and cost across the phase** (estimates from each §9, not measured; prices from Foundation §6.2)
- C1, C2: no external calls.
- C3: 11 Cohere embed calls to record once (2 per full Corpus D build of 97 chunks), plus a 1-call canary per scheduled run.
- C4: 4 Cohere calls, or 0 new calls if C3's recordings are reused.
- C5: 38 Groq calls on the 10 seeds (both citation arms, the context swap and one variance sample). Its 10 inline-citation calls are the same requests as C6's seed run, so they are recorded once. Add 110 calls once the M1 set exists. Optional Claude: 30. A 55-question Groq run costs about $0.012–0.021; Haiku about $0.019–0.033; Sonnet about $0.38–0.66.
- C6: 10 seeds = 12 Cohere calls + 10 Groq calls (about $0.002, about 2 minutes). A 55-question set = 55 + 55 calls (about $0.015, at least 14 minutes at 8K tokens/min).
- C7: about 75 Groq calls (about $0.03; at least 19 minutes; about 75% of a day's 200K-token Groq quota, which plan this applies to is **UNVERIFIED**), plus an optional Haiku arm of 45 calls (about $0.03).
- Cohere embed prices are **UNVERIFIED**, so their cost columns stay empty until `prices.json` holds a dated price.
- **Money is not the limit; Groq's rate limits are.** Every run is planned to resume from the cache.

---

## Concept C1: Document loading and parsing

### 1. Sources checked
**Book pages (opened 2026-10-17; text extracted with PyMuPDF 1.26.7 into the scratchpad, deleted after).**

| Page | What it says (paraphrased) | Used for |
|---|---|---|
| Ch1 p.4/14 | Step 1 Load: a PDF is parsed page by page into plain text; weak extraction weakens everything after it; librarian copying a book onto index cards | Core claim of C1 |
| Ch1 p.5/14 | Step 3 Clean: tabs, extra spaces, broken line endings; dirty text gives noisy embeddings | Cleaning (comes after Step 2 split) |
| Ch1 p.7/14 | Algorithm sketch: load → split → clean each chunk → embed → store | The book's order: clean **after** split |
| Ch1 p.13/14 | A trade-off table (Factor / Impact) | Specimen: a table that comes out one cell per line |
| Ch2 p.4/11 | A PDF gives one continuous text stream; a CSV gives rows | Why page records matter; bridge to C7 |
| Ch3 p.1/14 | A retrieved chunk that is a page footer full of links scored well and added noise | The header/footer symptom |
| Ch3 p.4/14 | A relevance filter drops boilerplate-only chunks | Downstream fix the book offers (V2), not a parser fix |
| Ch7 p.3/11 | Running headers in a printed book as the analogy for contextual chunk headers | Contrast: a *useful* added header (I5) vs repeated page-header *noise* (C1) |
| Ch14 p.4–5/13, p.9/13 | Summaries and chunks carry page or section metadata; the simplest scheme is page numbers | Page provenance pays off later (R5) |
| Ch16 p.1/11 | Standard RAG reads paragraphs and headings but skips figures, image tables and diagrams | What text extraction cannot see |
| Ch16 p.4/11 | Step 1: extract text and images separately; each image tagged with its page | Page-tagged extraction |
| Ch16 p.5/11 | Only the figure description of the p.4 diagram, then Step 2 (captioning) | 02's "p.4–5/11" is really p.4 (p.5 is captioning) |
| Ch16 p.10/11 | Captioning is overkill when the parser already gives tables as structured text | Parser table quality decides whether S2 is needed |

Book search over all 25 PDFs (pattern: pars*, PDF, clean, header, footer, OCR, layout, column, boilerplate, scanned, metadata): no hyphenation, ligature, reading-order, two-column, OCR or named-library text anywhere. The book's own PDFs end many chapters with the same website-name footer line (e.g. Ch1 p.14/14, Ch16 p.11/11): a real repeated-line specimen, as the existing lesson's S8 found in `intro.pdf`.

**Repo (pinned `009adba2be1bef49780ef73b6dd3c18fd24b035b`; HEAD checked with `git rev-parse`).**

| Location | Checked | What it shows |
|---|---|---|
| `helper_functions.py:L18-L31` | yes | `replace_t_with_space`: tabs only |
| `helper_functions.py:L48-L76` | yes | `encode_pdf`: `PyPDFLoader` (L62–L63), split (L69), **then** clean (L70); `length_function=len` (L67) |
| `helper_functions.py:L223-L245` | yes | `read_pdf_to_string`: `fitz.open` (L237), `content += page.get_text()` (L244): pages glued, no page numbers |
| `helper_functions.py:L1`, `L10` | yes | imports `PyPDFLoader` (langchain_community) and `fitz` |
| `simple_rag.ipynb` cell 10 | yes | its own `encode_pdf`: same loader and split-then-clean order |
| `multi_model_rag_with_captioning.ipynb` cell 8 | yes | two empty lists only |
| `multi_model_rag_with_captioning.ipynb` cell 9 | yes | PyMuPDF `get_text().strip()`, `page_number+1`, `get_images(full=True)`; its PDF (`attention_is_all_you_need.pdf`) is not in the repo |
| `Agentic_RAG.ipynb` cells 25–29 | yes (new) | A hosted vendor parser (Contextual AI `/parse`, VLM + OCR, `enable_document_hierarchy`). Vendor claims, no measurement; sends documents to a SaaS, so outside our decisions. Read-only example of "managed parsing" |

No repo code uses pdfplumber, unstructured, docling, marker, `PyMuPDFLoader` or `pymupdf4llm` (grep over `*.ipynb`, `*.py`, `*.md`, `*.txt`).

**Existing course files audited:** `concepts/C1_document_parsing.md` (Parts A–M, 698 lines, written 2026-10-08, before the house style); `labs/C1_parsing_lab.ipynb` (9 tasks, CHECK cells); `sources/verification/C1/C1_FACTS.md` (S1–S12, S-src) and its scripts (`c1_ref.py`, `c1_zoo.py`, `c1_measure.py`, `c1_crossversion.py`, `c1_sources.py`); 02 C1 card (L304–L323); 03 rows (L37–L38, L64–L65, L129, L279, L409, L415); 04 C1 row (L134) and DV-02 (L991); 06 §2.4, §2.5, §3.1, §5.1–§5.3; 08 D-01, D-02, D-17, RK-05, RK-18, A-05, Gate B items R-2/DEC-3. No `study/reading/C1_*` or `study/questions/C1_*` exists. Tracker: C1 `not_started`; P2 `not_started`; P1 `exposed`. Misconception log: none of MC-001…MC-006 is about parsing; MC-001 (tokens = characters) touches the "chars vs tokens" bridge only.

**AI Eval book (paraphrased, not quoted):** AE Ch8, 'PDF Documents': extraction is often the largest error source for PDF inputs; born-digital PDFs extract cleanly, scanned ones do not; table layout given to the LLM (row-wise vs column-wise) can change results; evaluate by inspecting the text the model actually saw, so extraction errors are not blamed on the model. AE Ch8, 'Debugging Multi-Step Traces': check PDF extraction as its own component before end-to-end tests. Both support C1's "component check before labelling" (RK-18).

**Interview repo** (`ombharatiya/AI-Engineer-Interview-Questions` @ `e080df2`, MIT, Copyright (c) 2026 Om), grep for pdf/pars/OCR/table:

| Item | Use for C1 |
|---|---|
| `04-rag-and-retrieval/questions.md` Q13 (detect silent parser corruption at scale) | **Hidden seed S6** in `sources/coach/transfer_seed_bank.md` (CR-13-eligible). Must **not** appear in the kit, the lesson or the tool's text. Its signals may be built into the tool only if the coach accepts the seed is spent (see Notes (e)) |
| `04-rag-and-retrieval/questions.md` Q16 (hardest part of enterprise RAG = parsing; toolbox in cost order; route by page difficulty) | Interview item (verbatim allowed with notice). Our answer must add: measure per corpus, freeze the snapshot |
| `04-rag-and-retrieval/questions.md` Q30 (tables and charts: keep structure; summary for retrieval, table for the generator; never split a table) | Bridge to C7/S2; one Full-only paragraph |
| `04-rag-and-retrieval/questions.md` Q14 (chunk metadata; "pipeline lineage": parser version, content hash) | Matches `snapshot_id`; good second interview item |
| `04-rag-and-retrieval/questions.md` Q3, Q46, Q47 (pipeline stages; triage; top failure modes incl. parsing corruption) | Context only; the "90% × 90% × 90%" line in Q3 is C6's seed, not C1's |
| `10-multimodal/questions.md` Q11, Q12 and `04-rag-and-retrieval/questions.md` Q52 (OCR vs VLM; tables and charts; ColPali) | Next (S2), link only |


**External sources** (opened 2026-10-17; details and limits in §5):
1. [C1-1] Livathinos et al. 2025, "Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion", AAAI-25 workshop, https://arxiv.org/abs/2501.17887 — verified (abstract and §5.4).
2. [C1-2] Ouyang et al. 2025, "OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations", CVPR 2025, https://arxiv.org/abs/2412.07626 — verified (abstract and v2 tables).
3. [C1-3] Adhikari & Agarwal 2024/2025, "A Comparative Study of PDF Parsing Tools Across Diverse Document Categories", arXiv preprint, https://arxiv.org/abs/2410.09871 — verified (abstract and v2 tables).
4. [C1-4] PyMuPDF 1.26.7 source as installed (`pymupdf.utils.get_text`, `TEXTFLAGS_*`, `Page.find_tables`, `table.py` L25–26) and https://pymupdf.readthedocs.io/en/latest/page.html — verified.
5. [C1-5] pymupdf4llm API docs, https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html — verified for the 1.28.2 docs; 0.2.9's parameters UNVERIFIED.
6. [C1-6] marker README, LICENSE and MODEL_LICENSE, https://github.com/datalab-to/marker — verified.
7. [C1-7] unstructured, "Partitioning", https://docs.unstructured.io/open-source/core-functionality/partitioning — verified.
8. [C1-8] langchain-community v0.4.2 `document_loaders/parsers/pdf.py` (GitHub tag `libs/community/v0.4.2`) — verified.
9. [C1-9] pdfplumber README, https://github.com/jsvine/pdfplumber — verified.
10. PyPI JSON API for every package in §10, and arXiv abstract pages for the 9 Corpus T candidates (§5.6) — verified.

### 2. Gap audit

Method as in the P3 audit: every idea from the book pages, the existing lesson (Parts A–M), the lab's 9 tasks, the Part L items, 02/06/08 and the research above. "Lesson" = `concepts/C1_document_parsing.md`. Tracker: P1 `exposed`; P2, P6, C2–C7, M1 `not_started` (and M1, S2, I2 have no lesson yet).

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **What a PDF page is**: glyphs drawn at x, y in content-stream order; no paragraphs, no reading order stored | Every artifact; why `sort=True` and `clip` exist | Incomplete: one bullet (D.1) | C1 | no | core | §1 of the lesson with a small drawn page (glyph boxes + stream order arrows) |
| 2 | **Born-digital vs scanned**: a text layer exists or not; OCR makes one, with its own errors | C1-T-01, empty vs image-only pages, the parser table | Incomplete: only "scanned page returns `''`" (D.4) | C1 (OCR itself: S2, out of scope) | no | core | Two sentences + the chars-vs-images test; OCR named, linked to S2 |
| 3 | Page record `Page(doc_id, page, text, parser)`, 1-based page | Lab T1, C2, citations | Yes (D.1) | C1 | no | core | Keep |
| 4 | `doc_text`, page table, who owns the join | Lab T2, T5, M1 | Yes (D.2, Part F) | C1 | no | core | Keep; it is the formula sheet's centre |
| 5 | **Character offsets and spans** (why a gold label is `[start, end)` on a frozen text) | D.3, J2, R-03 | Incomplete: assumed from M1, which has no lesson yet | M1 (C5 citations) | no | bridge | One paragraph + the bookmark picture (Part C) before D.3 |
| 6 | **What a hash is**: any byte change → a new value; sha256 prefix as an id | `snapshot_id`, lock file, R-02 | Missing (used from D.3 on) | O2 / C1 | no | bridge | Three-line bridge with a one-character demo (S3 row "one extra space") |
| 7 | `snapshot_id` recipe and what changes it | Lab T3, C3 manifest, J2 | Yes (D.3, S3 table) | C1 | no | core | Keep |
| 8 | **Unicode basics**: code point vs byte vs glyph; UTF-8; a ligature is one code point; normalisation forms; NFKC changes lengths | D.4 ligatures, R3, the Windows-bytes trap, T's 0–160 changed characters | Missing: "NFKC letters" is used without explanation | C1 (P1 owns chars vs tokens) | P1 exposed, rest no | core | A short "characters are not bytes" box + the NFKC length table (§5.3) |
| 9 | `"\n"` vs `"\r\n"` on Windows | Lab T4, J3 | Yes (D.3) | C1 | no | core | Keep |
| 10 | Artifact catalogue (hyphen, ligature, header/footer, columns, table, figure, empty vs image-only, page-break cut) | D.4, lab T6–T7, R-04 | Yes, but measured only on D and the zoo | C1 | no | core | Add the T probe column (§5.6) once T is chosen; until then label D-only numbers as D-only |
| 11 | **Reading order** and why it is a property of the PDF, not the parser alone | D.4, J5 | Incomplete and partly misleading (E-C1-5) | C1 | no | core | Show: zoo (fails), a LaTeX paper (mostly fine), `sort=True` (merges lines) |
| 12 | Hard hyphen vs soft hyphen (U+00AD) vs compound hyphen | R2, C1-A4 | Incomplete (soft hyphen counted in S5, never explained) | C1 | no | core | One table row each |
| 13 | Header/footer rule R1 and its false positives | D.5, J4 | Yes | C1 | no | core | Keep; add RAPTOR's running header as the real T case |
| 14 | **Tables**: detection strategies (ruling lines vs text alignment), what "flattened" means, Markdown output, measured weakness on scientific pages | D.4 table row, Ch16 p.10/11, AIQ Q30 | Incomplete: only "`find_tables` found 0" | C1 (C7 rows; S2 images) | no | core + next | Core: detection and flattening with one example; next: table summaries (C7/S2) |
| 15 | Figures are invisible to text extraction | D.4, Ch16 p.1/11 | Yes | S2 | no | next | Link only |
| 16 | Edits with an offset map (`src[i]`), undo | D.5, lab T8, Part F step 4 | Yes | C1 | no | core | Keep |
| 17 | Why v0 does no cleaning; cleaning = new snapshot | Part K, R-03 | Yes, but the evidence is D-only | C1 | no | core | Keep, and say T may justify R2/R3 later (E-C1-6) |
| 18 | **The parser landscape** (PyMuPDF, pymupdf4llm, pdfplumber, pypdf, unstructured, Docling, marker): what each gives, cost, licence | Interview Q16; any "why PyMuPDF?" question | Missing (only pypdf vs PyMuPDF) | C1 | no | core (Full) | One comparison table (§5.2) in Full; Short keeps "cheap text extractors vs layout models vs VLMs" |
| 19 | **Licences**: AGPL (PyMuPDF), arXiv non-exclusive vs CC BY for corpus files | Corpus T choice, A-05 | Missing | C1 | no | core (Full) | Two lines + the T candidate table |
| 20 | **Measuring parse quality**: per-page signals, a stratified hand sample, a two-parser diff | 02 evidence (artifact log), RK-18, C1-T-01 | Incomplete (T-01 only) | C1 | no | core | Taught through the apply-it tool; the at-scale scenario stays out of the lesson text (hidden seed S6) |
| 21 | **Retrieval vs answer quality**: a parser change matters only through questions on affected pages | Part I, T-01 key point "fraction of gold answers on flagged pages" | Incomplete (P6/M2 not studied) | P6, M2 | no | bridge | Two sentences in Short: Hit@k on flagged-page questions vs the rest |
| 22 | Characters vs tokens | M.4 link; page sizes | Link only | P1 | exposed (MC-001 open) | bridge | One sentence; do not re-teach |
| 23 | LangChain loader defaults: 0-based `page`, per-page `.strip()`, `"\n\f"` join, `extract_tables` appended to text | D.6, LLMOps notebook | Incomplete (0-based only) | C1 (LLMOps) | no | core (Full) | A defaults table in the LLMOps notebook; one line in Full |
| 24 | PDF lock (bytes) vs snapshot (text) | Part E, DEC-3 | Yes | C1 | no | core | Keep |
| 25 | Sentences cut at page breaks | D.4, C2 `scope: per_page` | Yes (measured) | C2 / I1 | no | next | Link |
| 26 | Equations become symbol soup | T papers | Missing | C1 (S2 for images) | no | core (Full) | One example row in the catalogue once T is chosen |
| 27 | Component evaluation (check extraction before blaming the model) | RK-18, AE Ch8 | Missing as a principle | C1 / M5 | no | core | One sentence in the answer-first box |

**Top gaps:** 8 (Unicode and NFKC), 11 (reading order taught from a synthetic case only), 14 (tables), 18–19 (parser landscape and licences), 20–21 (measuring parse quality and tying it to retrieval). Ideas 5 and 6 are small bridges but are used from D.3 onwards.

### 3. Quiz coverage

No `study/questions/C1_questions.md` exists, so this lists (a) which existing Part L key points a future **Short** reading must teach, and (b) the question titles the kit file needs.

**(a) Existing Part L items: key points that today live only in Full material (or nowhere)**

| Item | Key point at risk | Where it is now | Short must add |
|---|---|---|---|
| C1-R-02 | "a new version changes the id even with identical text" | D.3 table (S3) | the S3 row "version 1.28.2, same text → new id" |
| C1-R-03 | the D evidence: rules change nothing; naive de-hyphenation damages 7 of 7 | D.4/D.5 tables | the one-line D result, labelled "Corpus D only" |
| C1-R-04 | how to **detect** each artifact | D.4 table only | a 2-column "artifact → one check" list |
| C1-A-02 | "the dataset must be rebound to the new snapshot (06 §5.3 rule 3)" | not taught in the lesson body | one sentence on rebinding labels |
| C1-A-03 | `.strip()` removes 70 characters on D; the parser string lacks a version | D.6 table (S4) | the three bugs as a checklist |
| C1-T-01 | Ch16 p.10/11 overkill rule; "fraction of gold answers on flagged pages" and retrieval metrics on those questions | not taught (needs P6/M2) | idea 21 bridge (§2) |

**(b) Question titles the kit file needs** (R/A/T, one interview item; new scenarios, none from the seed bank)

| Id | Set | Title |
|---|---|---|
| C1-PRE-01 | pre | What comes out of a parser for each page, and what must travel with it? |
| C1-PRE-02 | pre | Two libraries give the same words. Are the character offsets the same? |
| C1-R-01 | main | The four fields of a v0 page record |
| C1-R-02 | main | The five inputs of the `snapshot_id`, and one change that alters it with identical text |
| C1-R-03 | main | Why v0 does no cleaning (with the Corpus D evidence) |
| C1-R-04 | main | Four artifacts, each with its detection check |
| C1-R-05 | main | Why whole-text NFKC is unsafe for a frozen snapshot (new) |
| C1-A-01 | main | Page starts from page lengths and the join (arithmetic) |
| C1-A-02 | main | One page added at the end: which rows change, does the id change |
| C1-A-03 | main | Find the three bugs in a one-line loader (0-based, `.strip()`, no version) |
| C1-A-04 | main | A page has 2 ligatures before offset 500; where does offset 500 land after ligature decomposition? (new; answer 502, derived) |
| C1-A-05 | main | Plan R2's edit for a hyphenated word and give the cleaned→raw map (new; extends Part F step 4) |
| C1-T-01 | main | Slide decks exported to PDF (existing practice item) |
| C1-T-02 | main | A results table in a two-column paper comes out one cell per line: what do you check, and how do you know whether it matters? (new; must not overlap seed S6) |
| C1-R-06 | interview | AIQ 04 Q16, "hardest part of enterprise RAG" (`source=AIQ-04-Q16`, MIT notice) |

Interview items stay within FORMAT's cap of 2 external items (Q16, plus Q14 as an optional review item).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| E-C1-1 | 02 C1 card `Pre: O2`; 04 C1 row `O2`; 03 dependency table L415 `C1 requires_all P2` and edge `P2 --> C1` (L279); lesson header "O2, P2" | Three files disagree on C1's prerequisite. 03 says P2 (mastery) and implies O2 only through P2; 02 and 04 say O2 | Read 2026-10-17 | Make one rule: `requires_all: O2`, `requires_exposure: P2` (C1 needs only "document, page, query" from P2, not its metrics). Record it in 03 and copy to 02/04 |
| E-C1-2 | 02 C1 card, Book | Lists only Ch1 p.5/14 and Ch16 p.4–5/11. Misses Ch1 p.4/14 (the Load step and "poor extraction → poor retrieval", the core claim), Ch1 p.7/14 (the sketch that shows clean **after** split) and Ch16 p.1/11, p.10/11. Ch16 p.5/11 is mostly captioning (Step 2); the extraction step is p.4/11 | Pages opened | Book: Ch1 p.4–5/14, p.7/14; Ch3 p.1/14; Ch16 p.1/11, p.4/11, p.10/11 |
| E-C1-3 | 02 C1 card, `Ext: none verified for PDF parsing (gap)` | Primary evaluations exist | [C1-1], [C1-2], [C1-3] | Cite them, with their limits (§5) |
| E-C1-4 | 04 C1 row (L134): "Parse page by page; **clean before chunking**" as the book's contribution | The book cleans **after** splitting (Ch1 p.5/14 Step 3 after Step 2; p.7/14 sketch). Already reported in the lesson's G.2 (2026-10-08) but 04 is still uncorrected | Ch1 p.4–5/14, p.7/14 | Correct in the next 04 pass, together with G.2's other three corrections |
| E-C1-5 | Lesson D.4 row "Two columns: lines alternate left, right"; J5 "A two-column paper gives nonsense sentences" | True for the synthetic zoo, which was drawn line by line across columns. On real LaTeX two-column arXiv papers PyMuPDF's default order is mostly column by column: 1–4 right→left jumps per paper over 10–16 two-column pages (scratchpad probe, PyMuPDF 1.26.7, 2026-10-17, heuristic). The lesson would make Yash expect garbage where there is little | §5 probe table | Say: "order follows the PDF's content stream; LaTeX papers are usually fine, slides and Word exports often are not; check a sample". Keep the zoo as the "what it looks like when it fails" case |
| E-C1-6 | Lesson Part I "n/a for C1" and H.4 "no numbers about T exist" | Fine for 2026-10-08, but the probe now shows Corpus T's dominant artifacts are **line-end hyphens (15–323 per paper) and ligatures (0–157)**, not columns. Corpus D had 7 and 0. So the lesson's evidence for "never de-hyphenate" (7/7 real compounds on D) does not transfer to T | §5 probe table | Lesson should state the D result as D-only and make the T artifact log decide R2 |
| E-C1-7 | Lesson D.6 / Verification log: the 37-character gap PyPDFLoader (72,523) vs raw pypdf (72,560) is UNVERIFIED | Likely cause found in source: langchain-community 0.4.2 (the version in LAB_FACTS §0) calls `.strip()` on every page (`parsers/pdf.py` L395–L399 `PyPDFParser`; L1010 `PyMuPDFParser`) | [C1-8] | Confirm with one local run in the verify notebook; then remove the UNVERIFIED |
| E-C1-8 | `c1_measure.py` output contains PyMuPDF's advisory "Consider using the pymupdf_layout package" | That package cannot be installed next to the pin: `pymupdf-layout` 1.26.6 requires `PyMuPDF==1.26.6`; later versions require 1.27+ | PyPI JSON 2026-10-17 | Lesson Full: one line, "ignore this advisory; layout mode is a separate-environment arm" |
| E-C1-9 | Foundation §12 row "2 · C1–C2" | Versioning is given as `params_hash` and trace focus as "chunk stats"; those are C2's. C1's version key is `snapshot_id` (06 §5.3), and its trace is per-page stats | Foundation L548 | C1 notebook versions by `snapshot_id` + `parser@version` + options; C2 by `params_hash` |
| E-C1-10 | 08 A-05 "use only open-licence documents (e.g. arXiv papers with permissive licences)" vs D-02's candidate list | 7 of the 8 candidates checked carry arXiv's **non-exclusive distribution licence** (not permissive); only RAPTOR is CC BY 4.0 (and Contriever, an alternate) | arXiv abstract pages, 2026-10-17 | Restate A-05 as "personal local use; never redistributed" (06 §5.2 already says this), or prefer CC-BY papers |
| E-C1-11 | 02 C1 failure line "hyphenation breaks and merged columns" | Fine as a list, but "merged columns" is mainly a problem of `sort=True` (it joins lines at the same height across columns, `get_sorted_text(tolerance=3)` in 1.26.7) and of non-LaTeX layouts, not of default extraction on LaTeX papers | PyMuPDF 1.26.7 source (`pymupdf.utils.get_text`) | Name the cause: "sorting by position, or a PDF drawn line by line" |

### 5. What the research says

#### 5.1 The three primary evaluations (study → result → limits → for this project)

**[C1-3] Adhikari & Agarwal 2024/2025, "A Comparative Study of PDF Parsing Tools Across Diverse Document Categories"** (arXiv preprint, not peer reviewed).
- **The study.** 10 tools (PyPDF 4.3.0, pdfminer.six, PyMuPDF 1.24.7, pdfplumber 0.11.2, pypdfium2, Unstructured 0.14.10, Tabula, Camelot, Nougat, Table Transformer) on 6 DocLayNet categories. Ground truth is DocLayNet's box text, joined in box order. Text metrics: token F1 (Levenshtein match ≥ 0.7), BLEU-4, local alignment. Tables: detection F1.
- **The result (scientific category).** Text F1 / BLEU: PyMuPDF 0.840 / 0.696; pypdfium2 0.853 / 0.709; pdfminer.six 0.851 / 0.658; Unstructured 0.851 / 0.663; PyPDF 0.764 / 0.583; pdfplumber 0.764 / 0.572. The authors say Nougat beats all rule-based tools on scientific text (a figure, no number). Table detection F1: Table Transformer 0.913; Camelot 0.339; PyMuPDF 0.179; pdfplumber 0.062.
- **Its limits.** A preprint. "800 documents per category" does not say pages or files. The F1 values of the rule-based table tools do not equal the harmonic mean of their own precision and recall, so treat those rows with care. Reading order is not evaluated on its own. Inline equations were not supported. Versions are from 2024.
- **For this project.** For **text** on born-digital papers, PyMuPDF is in the top group, so the pin costs little. For **tables**, no rule-based tool is good on scientific papers. Table questions in Corpus T need a check by eye, and table-heavy pages are a known risk (RK-18).

**[C1-1] Livathinos et al. 2025, "Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion"** (AAAI-25 workshop; CC BY 4.0).
- **The study.** Speed only: 89 PDFs, 4,008 pages (DocLayNet-based plus CCpdf). Docling 2.5.2, Marker 0.3.10, MinerU 0.9.3, Unstructured 0.16.5 (`hi_res`), on an 8-vCPU x86 CPU, an M3 Max and an L4 GPU.
- **The result.** Seconds per page on the x86 CPU: Docling 3.1, MinerU 3.3, Unstructured 4.2, Marker over 16. On the L4 GPU: 0.49, 0.21, no GPU gain, 0.86.
- **Its limits.** No accuracy numbers (deferred to future work). SaaS tools excluded. Late-2024 versions. No PyMuPDF or pdfplumber baseline.
- **For this project.** Corpus T is about 90–100 pages. At about 3 s/page, a Docling arm takes roughly 5 minutes per full parse on a CPU laptop, if Yash's laptop matches that CPU (**UNVERIFIED**). Fine for a one-off comparison arm, too slow for every rebuild.

**[C1-2] Ouyang et al. 2025, "OmniDocBench"** (CVPR 2025).
- **The study.** 981 annotated pages of 9 document types (129 academic pages). Metrics: normalised text edit distance, table TEDS, reading-order edit distance, formula CDM. Pipeline tools and vision-language models.
- **The result (English, end to end).** MinerU 0.9.3: text edit 0.061, table TEDS 78.6, order edit 0.079. Marker 1.2.3: 0.080, 67.6, 0.114. GPT-4o: 0.144, 72.0, 0.128. Academic pages, text edit: MinerU 0.025, Marker 0.059, GPT-4o 0.146.
- **Its limits.** No PyMuPDF, pdfplumber, pypdf, Docling or Unstructured. It **ignores headers, footers, page numbers, footnotes and captions** when scoring, which are exactly the lines that pollute RAG chunks. It scores Markdown made from page images, on Chinese and English pages.
- **For this project.** Layout-aware tools beat vision-LLMs on clean academic pages, but the benchmark cannot tell us what PyMuPDF loses on our files. A benchmark score belongs to its pages, not to our corpus, so we measure on T ourselves (AIQ 04 Q16; AE Ch8, 'PDF Documents').

#### 5.2 The parsers, side by side (born-digital, two-column technical PDFs)

| Parser | Extracts | Layout and tables | Page provenance | Licence | Install weight | CPU speed | Offline |
|---|---|---|---|---|---|---|---|
| **PyMuPDF** 1.26.7 (pinned) | text, words, blocks, `dict` spans with bbox and fonts, images | `sort=True` sorts by position and merges same-height lines across columns (`get_sorted_text(tolerance=3)`); `clip=` per column; `find_tables()` (lines / lines_strict / text; partly ported from pdfplumber, `table.py` L25–26); `TEXT_DEHYPHENATE` flag off by default; ligatures kept (`TEXTFLAGS_TEXT` = 195) | per page, 0-based index | **AGPL-3.0** or Artifex commercial | one wheel, about 18 MB (win_amd64), no Python deps | fastest class (on T: **UNVERIFIED**) | yes |
| `pymupdf4llm` 0.2.9 | Markdown per page; `page_chunks=True` gives a 1-based `page_number`, TOC items, table boxes (per the 1.28.2 docs; 0.2.9 parameters **UNVERIFIED**) | headers from font sizes; tables via `find_tables`; **layout mode** (page-header/footer, formula classes) needs `pymupdf-layout`, which needs another PyMuPDF version | per page | AGPL-3.0 | small (`tabulate`) | close to PyMuPDF (**UNVERIFIED**) | yes (OCR needs Tesseract) |
| pdfplumber 0.11.10 | chars with coordinates and fonts, words, lines, rects | `extract_text(layout=True)` is experimental; detailed table settings (lines, text, explicit); `crop`/`within_bbox` for columns; no OCR; "best on machine-generated PDFs" | per page | MIT | pdfminer.six + pypdfium2 + Pillow | slower than PyMuPDF (not measured) | yes |
| pypdf 6.19.0 | text (`plain` or `layout` mode) | no tables, no layout model | per page; LangChain adds `page_label` | BSD-3-Clause | pure Python | moderate (not measured) | yes |
| unstructured 0.27.10 | typed elements (Title, NarrativeText, Header, Footer, Table, PageBreak) | `fast` = pdfminer; `hi_res` = layout model (`detectron2_onnx`), the only strategy that extracts tables; OCR via Tesseract | per element (details **UNVERIFIED**) | Apache-2.0 | heavy: spaCy, numba, lxml, plus `[local-inference]` models; Python ≥ 3.11 | `hi_res` 4.2 s/page [C1-1] | yes after model download |
| Docling 2.133.0 | `DoclingDocument`: reading order, sections, tables (TableFormer), figures, formulas; Markdown/JSON export | layout model + table-structure model | per item `prov` (page + bbox) | MIT code (`docling-ibm-models` 4.0.3 MIT); model-weight licence **UNVERIFIED** | heavy: torch (already installed, CPU 2.14.1), torchvision, docling-parse, pypdfium2, plus a model download (size **UNVERIFIED**) | 3.1 s/page [C1-1] | yes after model download |
| marker 2.0.0 | Markdown/JSON/HTML with tables and LaTeX equations | Surya layout + OCR models; optional LLM pass (`--use_llm`, default Gemini) | per block | **code Apache-2.0 since 2.0.0 (1.10.2 was GPL-3.0-or-later); weights: modified OpenRAIL-M** (research, personal use, startups under $5M) | heaviest: torch, transformers ≥ 5.12.1, surya-ocr, **`anthropic<1`, `openai`, `google-genai`** | Marker 0.3.10: over 16 s/page on CPU [C1-1]; README speeds are on a B200 GPU host | models yes; LLM mode is an API |

**What this means.** On born-digital text the cheap parsers are already good [C1-3]. The model-based parsers buy **structure**: reading order on hard layouts, tables, formulas, header/footer labels. They cost 3–16 s per CPU page and hundreds of MB. For Corpus T the question is not "which parser is best" but "which pages break, and does a better parser fix the questions that touch them". That is a measured comparison arm, never a silent swap.

**For your project.** PyMuPDF stays the v0 parser and the only one in the v0 snapshot (pin 1.26.7). One comparison arm is worth it: **Docling** (MIT, no conflict with the pin, torch already present). pdfplumber is a light second opinion for tables. marker is out: it conflicts with the Foundation's `anthropic` 1.11.0, pulls in the OpenAI SDK and is slow on CPU. Each arm gets its own `snapshot_id` (`parser=docling@2.133.0`), so its offsets never mix with v0's.

#### 5.3 Current practice and pitfalls (with evidence)

| Topic | What practice does (2024–2026) | Pitfall, with evidence | For C1 |
|---|---|---|---|
| Header/footer detection | Layout models label `page-header`/`page-footer` (pymupdf4llm layout mode, Docling, unstructured `Header`/`Footer`); the cheap rule is "a line repeated on most pages" | Rules have false positives: R1 flagged 5 real section titles in the book's `index.pdf` (lesson S8). OmniDocBench drops these lines from scoring [C1-2]. RAPTOR's "Published as a conference paper at ICLR 2024" repeats on every page (probe, §5.6) | Keep R1 as a **report**; T will exercise it |
| De-hyphenation | `TEXT_DEHYPHENATE` (PyMuPDF) or a dictionary rule | It joins real compounds (on D, 7 of 7 would be damaged); after interleaved columns it glues across columns ("extracreading", zoo). On T there are 15–323 line-end hyphens per paper (probe), so R2 now matters | R2 (join only if the joined word occurs elsewhere) as a logged edit; T's log decides |
| Ligatures and Unicode | Decompose ligatures (flag off, or NFKC on U+FB00–FB06 only) | Whole-text **NFKC changes length and meaning**: `ﬁ`→`fi` (+1 char), `…`→`...` (+2), `½`→`1⁄2` (+2), `x²`→`x2` (the exponent is lost). On DPR it adds 108 characters (88 are `ﬁ`); on BERT 160; on Corpus D 0 (probe). Every later offset shifts | Never NFKC the snapshot. R3 maps ligature characters only, as logged edits with a `src[i]` map (as `c1_ref.py` L141–L159 already does) |
| Reading order (two columns) | Default content-stream order; position sort; per-column `clip`; layout models | LaTeX papers: mostly fine by default (1–4 right→left jumps per paper, probe). `sort=True` merges same-height lines across columns. Word and slide exports often fail | Check order on a sample page per document by eye; flag pages with many jumps |
| Tables | `find_tables()` → Markdown; Table Transformer / TableFormer for scientific tables | Rule-based detection on scientific pages is weak (PyMuPDF F1 0.18, pdfplumber 0.06; Table Transformer 0.91) [C1-3]. A flattened table loses its row–column links (AIQ 04 Q30). AE Ch8 notes that row-wise vs column-wise table text changes model results | v0 keeps raw text; table questions are an eval category; tables as Markdown = a later arm |
| Equations | marker and Docling emit LaTeX | Plain extraction gives symbol soup; NFKC makes it worse | Report the share of equation-like lines; no fix in v0 |
| Page provenance | Per page (PyMuPDF), per element with bbox (Docling, unstructured) | LangChain loaders store a **0-based** `page` and `.strip()` every page [C1-8]; the repo's `read_pdf_to_string` drops pages | 1-based `page` in every record; never strip; assert it |
| Cleaning vs frozen offsets | Keep raw originals and re-parse when tools improve (AIQ 04 Q16); lineage on every chunk (AIQ 04 Q14) | Editing text in place moves every later offset (06 §5.3; lesson D.5) | Cleaning = edits with a map, a new `cleaning` version, a new `snapshot_id` (06 §5.3 rule 2) |
| Quality at scale | Per-page signals: text vs images, gibberish share, repeated lines, table sanity; diff two parsers on a sample (AIQ 04 Q13, a hidden seed) | A library's benchmark score does not transfer; failures cluster by template | The apply-it tool (§8) |

#### 5.4 How to evaluate parsing (separate from answer quality)

1. **Extraction quality on its own** (a component check, AE Ch8): per-page signals (§8), a hand check of a stratified sample, and a diff against a second parser. Pass or fail per page.
2. **Does it matter for retrieval?** Only through the eval set. Build the same index (C2–C3) from two snapshots. Compare CE@k and Hit@k on the questions whose gold spans fall on flagged pages, and separately on the rest. Gold spans belong to one snapshot, so the second arm needs its spans re-validated (06 §5.3 rule 2) or a page-level relevance rule.
3. **Answer quality** is a third measurement (C5, M3), never mixed with 1 and 2.
4. **Baseline:** v0 = PyMuPDF `get_text()`, no cleaning, `snapshot_id` recorded.

#### 5.5 Interview angle

1. "What is the hardest part of RAG over enterprise documents?" (AIQ 04 Q16, MIT): parsing; the failure types; tools in order of cost; route by page difficulty; never index broken pages.
2. "What metadata goes on each chunk?" (AIQ 04 Q14, MIT): page, `doc_id`, offsets, parser version and content hash, which is our `snapshot_id`.
3. "Two parsers give the same words. Are your gold labels still valid?" No: offsets need byte-identical text (lesson S11).
4. "Would you NFKC-normalise the corpus?" Only with an offset map, never in place (§5.3).
5. "How do you handle tables?" Keep the structure (Markdown or HTML), a summary for retrieval, the table for the generator, never split a table (AIQ 04 Q30; C7 and S2 later).

#### 5.6 Corpus T candidates (a proposal; DEC-3 is Yash's choice)

Checked 2026-10-17: each arXiv abstract page opened, its licence link read, the PDF downloaded **to the scratchpad only** and probed with PyMuPDF 1.26.7 default `get_text()`. The probe is a heuristic; nothing was saved in the course. "Two-col pages" = pages with at least 2 long text blocks on each half. "Tables" = `find_tables()` hits (it over-counts). "Hyphens" = letter + `-\n` + lower-case letter.

| # | Paper (version) | Licence | Pages | Two-col pages | Tables found | Ligatures / line-end hyphens | Why it fits 06 §5.1 |
|---|---|---|---|---|---|---|---|
| 1 | Lewis et al. 2020, RAG (2005.11401v4) | arXiv non-exclusive | 19 | 2 | 6 | 114 / 47 | Overlaps DPR (its retriever), so near-duplicates; single-column NeurIPS layout with appendix tables |
| 2 | Karpukhin et al. 2020, DPR (2004.04906v3) | arXiv non-exclusive | 13 | 12 | 10 | 92 / 225 | **Two-column, tables, equations** (EMNLP); overlaps 1 and 3 ("dense", "retrieval") |
| 3 | Gao et al. 2022, HyDE (2212.10496v1) | arXiv non-exclusive | 11 | 8 | 14 | 70 / 156 | Two-column ACL style, result tables; shares DPR/Contriever baselines |
| 4 | Liu et al. 2023, Lost in the Middle (2307.03172v3) | arXiv non-exclusive | 18 | 15 | 15 | 0 / 259 | Two-column TACL, many tables and figures; feeds X3 later |
| 5 | Sarthi et al. 2024, RAPTOR (2401.18059v1) | **CC BY 4.0** | 23 | 1 | 8 | 0 / 81 | The only permissive licence among the RAG papers; a **running header on every page** (R1 test case); feeds R5 |
| 6 | Devlin et al. 2018, BERT (1810.04805v2), non-RAG | arXiv non-exclusive | 16 | 15 | 19 | 157 / 323 | Two-column NAACL, many tables; close to DPR (its encoder), so its "non-RAG" diversity is partial |
| 7 | He et al. 2015, ResNet (1512.03385v1), non-RAG | arXiv non-exclusive | 12 | 10 | 28 | 109 / 157 | Vision domain; two-column CVPR; dense result tables and equations: the hardest table case |
| 8 | Vaswani et al. 2017, Attention Is All You Need (1706.03762v7), non-RAG | arXiv non-exclusive | 15 | 1 | 5 | 0 / 15 | The repo's captioning notebook uses this paper (cell 9), so it links to S2; mostly single-column |
| alt | Izacard et al. 2021, Contriever (2112.09118v4) | **CC BY 4.0** | not downloaded | — | — | — | A permissive alternative to HyDE or DPR for the overlap criterion |

- **Two example sets** (Yash may swap any file): (a) 2 + 3 + 4 + 5 + 6 + 7 = 93 pages; (b) 1 + 2 + 4 + 5 + 7 + 8 = 100 pages. Both meet criteria 2 (two-column with tables), 3 (overlapping pairs) and 4 (≤ ~150 pages). Criterion 1 (Yash cares about the content) is Yash's call. Criterion 5: all are fine for personal local study; only the CC BY papers allow redistribution, under their terms.
- **What the probe changes in the C1 plan:** hyphens and ligatures dominate, not column interleaving (E-C1-5, E-C1-6); RAPTOR is the only file with a repeated running header; NFKC would shift DPR by 108 and BERT by 160 characters.
- **Caveat (08 REVIEWER NOTE on D-02):** all eight papers are famous, so the LLM has likely seen them; the closed-book control stays.
- Full sha256 values are computed at DEC-3 (the probe printed 12-hex prefixes, e.g. DPR v3 `3e67fc1a9977`, RAPTOR v1 `01319e2e6e6e`). A re-download can change the bytes, so hash the bytes (06 §5.3 rule 1).

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
A PDF stores glyphs drawn at positions, not paragraphs, so a parser has to rebuild the text, and every later stage only sees what it rebuilt. v0 reads each page with PyMuPDF 1.26.7, keeps a 1-based page number with the raw text, and freezes all pages into one joined text whose `snapshot_id` names the exact parser, version, options and cleaning. Chunks, citations and gold labels all point into that frozen text by character offset, so any change to the text, even one character or one Unicode normalisation, is a new snapshot. Extraction leaves artifacts: on Corpus D almost none, but on two-column arXiv papers hundreds of line-end hyphens, ligatures, tables flattened into one cell per line, equations and running headers. v0 cleans nothing; it measures the artifacts per page, and a cleaning rule or a second parser enters only as a new, logged snapshot that must beat v0 on the questions that touch the affected pages.

**The theory in one read (12 linked ideas).**

| # | Idea | Formula or rule |
|---|---|---|
| 1 | A page is drawn glyphs in content-stream order | text = parser(glyphs, order); order ≠ reading order in general |
| 2 | Text layer vs no text layer | chars(page) = 0 and images(page) > 0 ⇒ scanned/image-only; = 0 and 0 images ⇒ blank |
| 3 | Page record | `Page(doc_id, page = i + 1, text = get_text(), parser = "pymupdf 1.26.7")` |
| 4 | One coordinate system | `doc_text = "\n".join(pages)`; start₁ = 0; startᵢ₊₁ = endᵢ + 1; endᵢ = startᵢ + len(pageᵢ) |
| 5 | Offset → page | page = the last row with start ≤ offset (bisect); the join character belongs to the page before |
| 6 | A hash names bytes | sha256(bytes); one changed byte ⇒ a different id |
| 7 | Snapshot id | `sha256("snapshot-v1|parser=b@v|options=…|cleaning=c|page_join=\\n|doc:sha…")[:12]` (06 §5.3) |
| 8 | Characters are not bytes | len(text) counts code points; UTF-8 bytes ≥ characters; Windows writes `\r\n` unless `newline="\n"` |
| 9 | Normalisation changes length | NFKC: `ﬁ` 1 → 2 chars, `…` 1 → 3, `x²` → `x2`; every later offset shifts by the sum of the deltas before it |
| 10 | Artifacts and their checks | hyphen: `[a-z]-\n[a-z]`; ligature: U+FB00–FB06; header/footer: same line on ≥ max(3, ⌈n/2⌉) pages, digits masked; columns: text blocks on both halves + right→left jumps; tables: `find_tables()`; figure: image area with no text |
| 11 | Cleaning as logged edits | edit = {page, start, end, before, after}; cleaned text + map `src[i]`; `undo(apply(edits)) == raw` |
| 12 | Parse quality is per corpus, judged on questions | compare snapshots by Hit@k / CE@k on questions whose gold spans lie on flagged pages vs the rest; answer quality measured separately |

**Formula-sheet items:** ideas 3, 4, 5, 7, 9, 10 (the checks), 11; plus "same words ≠ same text" (pypdf vs PyMuPDF: 33/33 vs 0/33 on D) and the Windows byte count (72,595 vs 73,727 bytes).

**Step-by-step outline (running example).** Corpus D is the running example for the mechanism (pages, page table, snapshot id: every number already measured in C1_FACTS). Corpus D is too clean to show artifacts (single column, no tables, 7 hyphens, 0 ligatures), so the artifact steps use the synthetic zoo (failures drawn on purpose) and, once Yash chooses, one Corpus T paper. Until DEC-3, the lesson shows T numbers only as "candidate probe, 2026-10-17" from §5.6.

1. The failure first: the repo's `read_pdf_to_string` gives 72,561 characters and no pages; where is "Paris Agreement"? (offset 13,420, but which page? You cannot say.)
2. What a page is (idea 1–2), drawn.
3. Load D into 33 `Page` records (idea 3); the 0-based trap.
4. Join, page table, `page_of` (ideas 4–5); Part F by hand.
5. Hash and `snapshot_id` (ideas 6–7); the S3 "what changes the id" table.
6. Characters, bytes, Windows (idea 8).
7. The artifact catalogue (idea 10): D (clean) → zoo (broken) → one T paper (real).
8. Unicode normalisation (idea 9): the NFKC length table; why R3 touches ligatures only.
9. Cleaning as logged edits (idea 11); why v0 applies none.
10. Parsers compared (§5.2), in one table; why PyMuPDF stays pinned and Docling is an arm.
11. Measuring parse quality (idea 12) → the apply-it tool.

**Visuals (each earns its place).**

| Visual | The one thing it shows |
|---|---|
| A drawn page: glyph boxes with numbered stream order, two columns | Order comes from the file, not from reading; why `sort=True` merges lines |
| Pages as bars on one ruler with the join characters marked | Offsets, the page table and who owns the join |
| "One change, new id" table with the changed input highlighted | What the hash protects |
| Offset-shift strip: a ligature decomposed at position 120 moves everything after it by 1 | Why NFKC in place breaks labels |
| Per-page bar chart (Plotly in the notebook; SVG in the lesson) for one T paper: chars, images, hyphens, flags | What the apply-it tool sees |
| Parser landscape: cost (s/page) vs what you get (text → structure), with licences as labels | Choosing a parser is a trade-off, not a ranking |

**Full only.** The full parser table with licences and install weight; LangChain loader defaults; `TEXTFLAGS_TEXT` bits; the three evaluations' numbers and limits; soft hyphens; equations; table strategies (lines vs text); the 37-character `PyPDFLoader` gap; the pymupdf-layout advisory (E-C1-8).

### 7. Verify notebook plan

`study/notebooks/C1_parsing_verify.ipynb`, one section per lesson step, in the P3 verify notebook's style (markdown claim → code → printed number → the C1_FACTS id it must equal → a pass/fail line).

| § | Recomputes | Data | Code | Must equal |
|---|---|---|---|---|
| 1 | `read_pdf_to_string` length and the lost page of offset 13,420 | Corpus D | repo function re-typed (3 lines) | 72,561; no page (S4) |
| 2 | 33 `Page` records, lengths min/max, total | D | `pymupdf.open`, `get_text()` | 636 / 2,494 / 72,561 (S2) |
| 3 | `doc_text`, page table, round trip, `page_of` | D | `bisect` | 72,593; rows p.1–3; "Paris Agreement" → (6, 1,874) (S2, S6) |
| 4 | `snapshot_id` and the 5 "one change" ids | D | 06 §5.3 recipe | `ea07572562ac` and the S3 table |
| 5 | Windows bytes | D | write twice | 72,595 vs 73,727 bytes (S7) |
| 6 | Artifact counts on D | D | lesson regexes | hyphens 7 (all compounds), ligatures 0, repeated lines none, 24/32 breaks (S5) |
| 7 | The zoo: interleaved order, `sort=True`, column clip, DEHYPHENATE trap, empty vs image-only, tables | zoo PDF built in-notebook by `c1_zoo.py`'s code | PyMuPDF | S9 values |
| 8 | NFKC length table and an offset-shift demo | literal strings; D (0 changes) | `unicodedata` | `ﬁ` +1, `…` +2, `½` +2; D delta 0 (probe, 2026-10-17) |
| 9 | Logged edits R1–R3, round trip | zoo, D | `plan_edits`/`apply`/`undo` (from `c1_ref.py`) | zoo: 92 removed, 6 inserted; D: 0 edits vs 7 naive (S10) |
| 10 | Reading-order probe (right→left jumps) and the per-page chart | zoo; **one Corpus T PDF if present** | blocks + Plotly bar chart | zoo fails; T values recorded once T is frozen |
| 11 | pypdf vs PyMuPDF "same words, different bytes" | D | **optional cell**: runs only if `pypdf` is importable, else prints the recorded S11 values | 0/33 identical, 33/33 same words (S11) |

- **Why two data sources:** Corpus D carries every mechanism number but almost no artifacts; the zoo shows failures on purpose. The T cell is skipped with a clear message until DEC-3 freezes T (the PDFs are not committed; the notebook reads the lock file's path).
- **API calls:** none. **Offline:** yes. **Runtime:** under 30 s on CPU (D is 33 pages; the zoo 5) (estimate; measure when built).
- **Book PDFs:** not used in the verify notebook (they are specimens in the full lesson only; printing their text risks copying).
- **Charts:** Plotly, two: per-page bars (chars, images, flags) and the offset-shift strip.

### 8. Apply-it tool plan and real-world checklist

**`study/tools/parse_quality_check.py`**: "Which pages of MY PDFs did the parser get wrong, and do my questions touch them?" Same shape as `bm25_fit_check.py` (CLI + importable `run_check` / `render_report`).

- **Inputs:** `--docs` files or folders (PDF; `.txt`/`.md` pass through as one page); optional `--questions` (`.jsonl` with `q` and `expect`, as in `bm25_fit_check`); `--sample N` pages for the hand check (default 8); `--second-parser {none,pdfplumber,pypdf}` (used only if importable); `--html` to write a side-by-side page (rendered page image next to its extracted text) for the sampled pages.
- **Parser:** PyMuPDF 1.26.7 `get_text()` exactly as v0, so the tool also prints the would-be `snapshot_id` (options `{}`, cleaning `none`).
- **Outputs:** a Markdown report (sections: corpus summary, per-document table, flagged pages with reasons, sample for the hand check, questions on flagged pages, checklist, recommendation) and `pages.jsonl` (one row per page with every signal: the "trace" the LLMOps notebook reuses).
- **No API calls.** Standard library + pymupdf; numpy only for summaries.

**Per-page signals (auto):**

| Signal | Computation | Flag when |
|---|---|---|
| Text vs images | chars; image count; image area share (`get_image_info`) | chars < 50 and images ≥ 1 → image-only (needs OCR or captioning); chars = 0 and 0 images → blank |
| Non-word share | share of tokens with no letter, or with characters outside `[A-Za-z0-9-']` after removing digits; mean word length | share above the document's median + 3 × MAD (relative, so maths-heavy papers are not all flagged) |
| Encoding failure | count of U+FFFD and `(cid:N)`-style strings | any |
| Repeated lines | rule R1 (digits masked; ≥ max(3, ⌈n/2⌉) pages) | report lines; show them, never delete |
| Line-end hyphens | `[A-Za-z]-\n[a-z]`; R2 split into "joined form attested elsewhere" vs not | report counts per page |
| Ligatures / NFKC | U+FB00–FB06 count; characters NFKC would change, and the length delta | report; delta > 0 means "never NFKC in place" |
| Columns and order | long text blocks on both halves; right→left jumps in block order | jumps ≥ 2 on a page |
| Tables | `find_tables()` count; per table, rows × columns and the share of empty cells | table found, or many short lines with numbers but no table found (suspected flattened table) |
| Equation-like lines | share of lines with > 30 % non-alphanumeric symbols | report |
| Page-break cut | page ends without final punctuation and the next starts lower-case | report (C2 problem) |
| Two-parser diff (optional) | word-level Jaccard between PyMuPDF and the second parser per page | Jaccard < 0.9 |

**Real-world checklist** (the report fills the verdicts: ✓ fine, ✗ problem found, ? check by hand):

| # | Check | Auto / manual |
|---|---|---|
| K1 | Every page has a text layer (no image-only or blank pages where text is expected) | auto |
| K2 | No encoding failures (U+FFFD, `(cid:…)`) | auto |
| K3 | Page numbers are 1-based and every page round-trips through the page table | auto |
| K4 | Repeated header/footer lines are listed, and each is confirmed as noise or a real heading | auto list + manual decision |
| K5 | Line-end hyphens: share whose joined form occurs elsewhere (R2 candidates) vs real compounds | auto |
| K6 | Ligatures and NFKC deltas recorded; no normalisation applied in place | auto |
| K7 | Two-column pages read column by column (right→left jumps ≤ 1 per page) | auto, then manual look at the worst page |
| K8 | Tables: found tables listed; suspected flattened tables listed; one table checked against the rendered page | auto + manual (open the `--html` page) |
| K9 | Figures with no extracted text: do any questions need them? | auto count + manual |
| K10 | Questions on flagged pages: how many `expect` strings fall on flagged pages | auto (needs `--questions`) |
| K11 | A stratified hand sample (by document × flag) was read side by side with the page image | manual, with the `--html` page |
| K12 | The would-be `snapshot_id` is recorded with the report | auto |

**Recommendation logic.**
1. Any K1/K2 failure on pages with questions → "this page needs OCR or captioning (S2); exclude or flag it before labelling" (RK-18).
2. K7 or K8 fails on pages that questions touch → "try a comparison arm (Docling, or `clip` per column) as a new snapshot; compare Hit@k on those questions".
3. Many R2 candidates or ligatures, and questions quote those words → "a cleaning version (R2/R3 as logged edits) is worth an experiment".
4. Nothing flagged on pages with questions → "v0 parsing is fine for this corpus; do not clean".
5. No questions given → "not enough data: the flags show risk, not harm".

**Boundary with the hidden seed.** The tool's signals overlap the hidden transfer seed S6 (AIQ 04 Q13). The tool's text must not pose the at-scale question, and the lesson must not either (FORMAT "Hidden seeds"). See Notes (e).

### 9. LLMOps notebook plan

`study/llmops/notebooks/C1_parsing_llmops.ipynb` (path per the Foundation §10 package plan). Foundation §12 row "2 · C1–C2" applies: **no external calls**, a loader comparison, T1 tests; with the correction in E-C1-9 (C1 versions by `snapshot_id`, not `params_hash`).

**External calls (cached):** none. No LLM, embedder or reranker. The notebook runs identically in `record`, `replay` and `auto` mode, with no key; the `replay` CI marker still executes it (it must not open a socket).

**Framework build (comparison only; the mechanism stays our loader).**

| Lesson step | Our code (mechanism) | Framework piece | Default the lesson warns about |
|---|---|---|---|
| Load pages | `load_pages()` → `Page(doc_id, page, text, parser)` | `langchain_community.document_loaders.PyMuPDFLoader(path, mode="page")` | `metadata["page"]` is 0-based (`page.number`); each page is `.strip()`-ed (`parsers/pdf.py` L1010, v0.4.2); `extract_tables="markdown"` **appends** tables to the page text, so the text is no longer a slice of `get_text()` |
| Load pages (repo's reader) | same | `PyPDFLoader(path)` (needs `pypdf`, which `langchain-community` does not install) | 0-based `page` plus `page_label`; `.strip()` per page (L395–L399); `mode="single"` joins with `"\n\f"`, not our `"\n"` |
| Snapshot | `build_snapshot()` → manifest, `snapshot_id` | none (LangChain has no frozen-text concept) | A `Document` list carries no parser version or text hash |
| Artifact report | `artifact_report()` / the apply-it tool | none | — |

- Cells compare per page: equal text? length delta; equal after `.strip()`? This should settle the 37-character `PyPDFLoader` gap (E-C1-7).
- `langchain-community` 0.4.2 prints a "being sunset" `DeprecationWarning` on import (LAB_FACTS §0). Show it; it is a reason to keep loaders out of the mechanism.
- Not used: `langchain-pymupdf4llm` (it requires `pymupdf4llm==1.28.0`, which conflicts with the pin; PyPI 2026-10-17). `langchain-docling` 3.0.0 exists (MIT) and would wrap the Docling arm; its release date was not checked against the 2-week rule (**UNVERIFIED**), and the arm can be read from Docling's own JSON instead.

**Tracing.** Per run: one root span (`run_id`, `corpus`, `snapshot_id`, `parser@version`, `options`, `cleaning`, `doc_text_sha256` per doc, git commit, timestamps) and one span per page with the §8 signals (chars, images, flags, hyphens, ligatures, NFKC delta, jumps, tables, parse time). **No page text** in exported spans. Default sink: the plain JSONL trace (Foundation §3.2). Local viewer: Phoenix (optional; nothing here needs it). LangSmith: only for Corpus D, and only stats (Foundation §3.2 privacy guard); Corpus T stays local (arXiv non-exclusive licences; never book text, which is never an input).

**Dataset and evaluators** (all code-based, tier 1; `code-based-evaluators`):
- A small **parse fixture set** (JSONL): for each frozen document, 5–10 `(page, expected substring, expected page offset)` rows checked by hand on the rendered page, e.g. D: "Paris Agreement" → page 6, offset 1,874. This is the C1 "golden set"; it grows when the apply-it tool finds a new artifact (error-analysis loop).
- Evaluators: `pages_are_1_based`, `page_table_round_trip`, `snapshot_id_recomputes`, `no_carriage_returns`, `fixture_substrings_at_offsets`, `no_encoding_failures`, `flag_rates_within_budget` (e.g. image-only pages = 0 where questions exist).
- Retrieval effect: **not** measured here (no eval set before M1). The notebook states the hand-off: v1.1/I2 compares CE@k on flagged-page questions between snapshots (`rag-evaluation`: retrieval kept separate from answer quality).

**Experiment against the previous version.** "Version" here = snapshot. Arm A: `pymupdf@1.26.7`, options `{}`, cleaning `none` (v0). Arm B (optional, one of): cleaning `r2r3_v1` (logged edits), options `{"clip": "columns"}`, or the Docling arm. Report per document: characters, flags per page, NFKC deltas, fixture pass rate, parse time p50/p95 per page, and the diff in `snapshot_id`. A decision needs the later retrieval comparison; this notebook only shows *what changed*.

**Cost, latency, tokens.** $0 and 0 tokens. Parse time per page (p50/p95) and full-build time per corpus are logged; the Docling arm's time is the main cost (about 3 s/page on CPU per [C1-1]; Yash's machine **UNVERIFIED**).

**Prompt and config versioning.** No prompts. Config = the `parsing:` block of 06 §2.4 (backend, mode, version, options, cleaning). Its values feed the `snapshot_id`; the manifest is the versioned artifact; a cleaning rule gets a version string (`r2_v1`) and is a new snapshot (06 §5.3 rule 2). Tie each change to a registry entry (06 §9.1) as Foundation §7 says.

**Monitoring and feedback.**
- **Canary:** re-parse Corpus D on every CI run and assert `snapshot_id == ea07572562ac`. A PyMuPDF upgrade that changes text fails loudly (this is how a 1.26.7 → 1.28.2 move would be checked; byte-identical on D per S11, unknown on T).
- **Watch:** per-document parse-quality rates from the apply-it tool's `pages.jsonl` over time (image-only share, encoding failures, flagged share); alert when a new document has > 10 % flagged pages or any encoding failure (threshold to calibrate on T).
- **Feedback:** a flagged page that a question needs → error-analysis log (M5 taxonomy: "parse corruption") → a new fixture row → a T1 test.

**Place in the lifecycle.** Analyze: the artifact log and flagged pages (`error-analysis`, `trace-data-analysis`). Measure: code evaluators above (`code-based-evaluators`). Improve: a cleaning rule or parser arm as a new snapshot (`improving-llm-agents` is not needed; there is no model). dev → CI → monitor: notebook → T1 + `replay` marker (`ci-cd-evals`) → the canary and the tool's logs. Tracing: `llm-observability`. Retrieval-vs-answer separation: `rag-evaluation`.

**Skills used:** `llm-observability`, `code-based-evaluators`, `ci-cd-evals`, `error-analysis`, `trace-data-analysis`, `rag-evaluation`, `evals-foundations`.

### 10. Tools, frameworks, libraries and LLMs

Pins: newest release on or before 2026-10-03, from the PyPI JSON API read 2026-10-17. "Installed" from `uv pip list` (read-only).

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| v0 parser (mechanism, snapshot) | `pymupdf` | **1.26.7 (pinned; keep)** | yes | yes | $0 | AGPL-3.0 or Artifex commercial | yes. Newest is 1.28.2 (2026-08-06); do not upgrade (snapshot_id) |
| Markdown per page (optional reading) | `pymupdf4llm` | 0.2.9 (2026-01-10; the last release that accepts pymupdf 1.26.x) | no | yes | $0 | AGPL-3.0 | yes, **without** the `[layout]` extra. 1.28.x needs pymupdf 1.28.2 → conflicts |
| Layout mode for PyMuPDF | `pymupdf-layout` | — | no | yes | $0 | AGPL-3.0 | **no**: 1.26.6 pins `PyMuPDF==1.26.6`, later ones 1.27+ (onnxruntime) |
| Second opinion, tables | `pdfplumber` (+ `pdfminer.six` 20260107, `pypdfium2`) | 0.11.10 | no | yes | $0 | MIT | yes (comparison arm only) |
| Repo parity (PyPDFLoader) | `pypdf` | 6.19.0 (2026-09-16; also the LAB_FACTS version) | no (was used in a scratch venv) | yes | $0 | BSD-3-Clause | yes (comparison only) |
| Layout-model comparison arm | `docling` | 2.133.0 (2026-10-03) | no | yes after model download | $0; ~3 s/page CPU [C1-1] | MIT (model weights **UNVERIFIED**) | **needs a decision**: heavy (torchvision, docling-parse, models; size **UNVERIFIED**). Uses the installed CPU torch; no pymupdf conflict. Prefer running it outside the lock (e.g. `uvx --from docling==2.133.0 docling …`; CLI flags **UNVERIFIED**) and saving its JSON as a separate snapshot |
| Typed elements | `unstructured` | 0.27.10 | no | yes (`fast`); `hi_res` after model download | $0 | Apache-2.0 | not recommended: heavy (spaCy, numba; `[local-inference]` for tables), no gain over Docling for this purpose |
| Marker | `marker-pdf` | 2.0.0 | no | models yes; `--use_llm` no | $0 (LLM mode = API) | code Apache-2.0 (1.x GPL-3.0+); weights modified OpenRAIL-M | **no**: requires `anthropic<1` (conflicts with Foundation `anthropic` 1.11.0), pulls `openai` and `google-genai`, >16 s/page CPU |
| OCR engine | Tesseract (system) | — | no | yes | $0 | Apache-2.0 | not needed: Corpus T is born-digital; out of scope (S2) |
| LLM per task | Groq `openai/gpt-oss-20b` / Claude | — | — | — | **0 calls** | — | C1 has no LLM step. Captioning or VLM parsing would be S2 (Phase 11) and needs a decision there |
| LangChain loaders (LLMOps notebook only) | `langchain-community` | 0.4.2 (2026-05-22) | no | yes | $0 | MIT | yes, comparison only. Pulls `langchain-classic`, `langchain-core`, `langsmith`, `sqlalchemy`, `aiohttp`; does **not** pull `pypdf`; prints a "being sunset" warning |
| Framework core | `langchain-core` | 1.6.6 (Foundation pin) | no | yes | $0 | MIT | yes |
| LangChain + Docling | `langchain-docling` | 3.0.0 (date not checked) | no | — | $0 | MIT | optional; **UNVERIFIED** pin |
| LangChain + pymupdf4llm | `langchain-pymupdf4llm` | — | no | — | — | GPL-family licence text (exact licence **UNVERIFIED**) | **no**: requires `pymupdf4llm==1.28.0` |
| Hosted tracing | `langsmith` | 0.14.4 (Foundation pin) | no | SDK yes | free plan; `LANGSMITH_API_KEY` | MIT | Corpus D stats only |
| Local tracing | plain JSONL trace (default); `arize-phoenix-otel` 0.17.2 (optional viewer client) | — | no | yes | $0 | ours / Apache-2.0 | yes |
| Tests | `pytest` | 9.1.1 | yes | yes | $0 | MIT | yes |
| Charts | `plotly` | 7.1.0 (keep) | yes | yes | $0 | MIT | yes |

**Install lines (do not run until the build is approved):**

```text
uv add --group parse-arms pdfplumber==0.11.10 pypdf==6.19.0
uv add --group parse-arms pymupdf4llm==0.2.9            # optional; never with [layout]
uv add --group llmops langchain-community==0.4.2        # with the Foundation llmops group (langchain-core==1.6.6, langsmith==0.14.4)
uvx --from docling==2.133.0 docling --help               # only if Yash says yes to the Docling arm; stays out of uv.lock
```

**Keys needed:** none for C1. `LANGSMITH_API_KEY` only if Corpus D stats are mirrored to LangSmith (optional, Foundation decision 3). **Heavy items:** Docling (and its models) is the only one; it stays out of the project lock.

### 11. Open questions for Yash (preferences only)

1. **Corpus T:** set (a), set (b) from §5.6, or your own mix from the candidates? (DEC-3; one word: a / b / mix.)
2. **Docling comparison arm:** run it once on Corpus T, outside the project lock (about 5 minutes per parse; model download size unknown)? (yes / no)
3. **Apply-it report:** include rendered page images next to the extracted text for the sampled pages (a larger HTML file, much faster hand checks)? (yes / no)

---

## Concept C2: Chunking fundamentals

### 1. Sources checked

**Book pages (all opened 2026-10-17, PyMuPDF text extract; paraphrased).**

| Page | What it says (paraphrase) | Verdict |
|---|---|---|
| Ch1 p.4/14 | Step 2 of preparation: split into chunks; the usual default is near 1,000 characters (about one long paragraph) plus 200 of overlap; overlap is said to keep a thought that spans two paragraphs, so nothing is lost "at the seams" | Verified. The overlap claim is an overclaim (true only for spans of at most O + 1 characters with fixed windows; never across a per-page cut) |
| Ch1 p.5/14 | Overlap figure (three chunks, shared bands); Step 3 cleans text (tabs, extra whitespace, broken line endings) | Verified. Note the **order**: the book cleans *after* splitting. Cleaning after splitting breaks the offset round-trip; v0 cleans nothing (06 §3.1) |
| Ch1 p.7/14 | Algorithm sketch: load → split ~1000/~200 chars → clean each chunk → embed → store | Verified. **Cited by 04 but missing from the 02 card** |
| Ch1 p.10/14 | "Role of chunk size": called the most important setting in simple RAG; too small (about 100 chars) lacks context | Verified. Asserted, not measured |
| Ch1 p.11/14 | Too large (about 5,000 chars) buries the signal; 1,000/200 called "just right" | Verified. "Just right" is corpus-, model- and question-dependent (I1 tests it) |
| Ch1 p.12/14 | Multi-section questions expose the limits of a few fixed chunks; RAG is overkill if documents fit in the context window | Verified (used for "when not to chunk") |
| Ch1 p.13/14 | Key takeaway repeats that overlapping chunks stop information loss at boundaries | Verified; same overclaim |
| App p.14/23 | Glossary "Chunk / Chunking" and "Chunk Overlap" (about 200 characters; again "no information is lost") | Verified; same overclaim |
| App p.16/23 | Glossary "Fixed-Size Chunking": regular character intervals, optional overlap, blind to idea boundaries | Verified. **Not cited anywhere in 02/04/07**; useful for the lesson |
| App p.6/23, p.12/23 | Layer 1 = fixed-size chunking first; Layer 2 recommends semantic chunking; measure before and after every change | Verified (forward links only) |
| Ch4 p.1–2/15 | A chunk packing three facts has a "blurry" vector that blends them | Verified (dilution bridge) |
| Ch7 p.1–2/11 | Chunks lose pronoun referents and section headings once cut out | Verified (fragmentation bridge; I5) |
| Ch8 p.1–2/11 | Overlap is "a partial fix"; boundaries are placed "by a character counter" | Verified. The book's own correction of Ch1. "Character counter" does not describe the repo's recursive splitter, which prefers separators |
| Ch9 p.1–2/14 | Fixed windows ignore topic shifts; a mixed chunk's embedding lands between topics | Verified (I3 link) |
| Ch6 p.9/14 | HyDE: match the hypothetical document's length to the chunk size | Verified (Q2/I1 link; not C2) |
| Whole book | No glossary entry and no definition for "token"; truncation not discussed | Glossary checked in the Appendix extract (no "token" entry); the whole-book claim rests on 03 §5 row 2 and 08 L147, not re-checked page by page |

**Repo cells and lines** (`upstream/RAG_Techniques` @ 009adba; 0-based cells; each opened from the .ipynb JSON):

| Cite | What is there | Verdict vs 02/04 |
|---|---|---|
| `simple_rag.ipynb` cell 10 | Local `encode_pdf(path, chunk_size=1000, chunk_overlap=200)`: `PyPDFLoader` → `RecursiveCharacterTextSplitter(chunk_size, chunk_overlap, length_function=len)` → `split_documents` per page → `replace_t_with_space` → embeddings via `get_langchain_embedding_provider(EmbeddingProvider.OPENAI)` → FAISS | Verified (02 correct). Cell 11 is the call with 1000/200 |
| `helper_functions.py:L48-L76` | The same `encode_pdf`, but with `OpenAIEmbeddings()` hardcoded (L73) | Verified |
| `context_enrichment_window_around_chunk.ipynb` cell 13 | `split_text_to_chunks_with_indices`: raw `text[start:start+chunk_size]`, stride `chunk_size - chunk_overlap`; cuts mid-word; stores the **whole text** in every chunk's metadata | Verified. Two more defects not named in 02: no `0 <= overlap < size` check (overlap ≥ size loops forever or goes backwards), and no stop when a window reaches the end, so it emits redundant tail chunks (the same bug as 07 C2-A-04) |
| `proposition_chunking.ipynb` cell 9 | `RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=200, chunk_overlap=50)` (tokens, default `gpt2` encoding) | Verified. Imports from the old path `langchain.text_splitter` |
| `reliable_rag.ipynb` cell 6 | `from_tiktoken_encoder(chunk_size=500, chunk_overlap=0)`; `CohereEmbeddings(model="embed-english-v3.0")` | Verified. 500 **gpt2** tokens sized for an embedder that counts in **its own** tokenizer: the unit mismatch C2 warns about |
| `document_augmentation.ipynb` cells 4, 6 | Constants 4000/100 and 128/16 "tokens"; `split_document` uses `re.findall(r'\b\w+\b')` and re-joins with spaces | Verified: "tokens" are regex words; punctuation lost |
| `choose_chunk_size.ipynb` cell 10 | LlamaIndex `Settings.chunk_size`, overlap `chunk_size // 5`, `similarity_top_k=5` | Verified (I1 material, read only) |

**Existing course files read:** `07_SAMPLE_LESSON.md` (all 1,857 lines; Parts A–H and J–M are C2, Part I is I1), `labs/C2_chunking_lab.ipynb` (cells 0–38), `sources/verification/C2lab/C2LAB_FACTS.md`, the `verify07/` file list, 02 card C2 (L327–L342) and §4 gates, 03 rows for C2, 04 rows C2 (L135) and the Ch1 table (L289), 06 §2.3, §2.4, §3.1, §3.2, 08 (C2 rows, tool table L197–L201), `EXTERNAL_RESOURCES_REVIEW_2026-10-09.md` (C2 item at L124; the C2 reserve seed in `sources/coach/transfer_seed_bank.md` L234 is hidden and must not enter the kit), tracker rows P1/C1/C2/C3/I1, `misconception_log.md` (MC-001 central), `study/FORMAT.md`, the P3 gap audit, P3 lesson headings, `bm25_fit_check.py` header, and the project skills `rag-evaluation`, `llm-observability`, `evals-foundations`, `code-based-evaluators`. No `study/questions/C2_questions.md` or `study/reading/C2_*.md` exists yet.

**AE book:** not needed for C2 (the review notes AE Ch7 promises a chunking grid-search section that is absent; that is I1/M1).

**Interview repo** (`ombharatiya/AI-Engineer-Interview-Questions` @ e080df2, MIT, "Copyright (c) 2026 Om"): `04-rag-and-retrieval/questions.md` Q4 ("What chunking strategies do you know, and how do you pick one?") and **Q5 ("How do chunk size and overlap affect retrieval quality, and what numbers would you start with?")**; `12-coding-challenges/09_text_chunking.py` (four chunkers tested by invariants; per the external review, use only as a 30-day re-implementation). Q5's answer starts at "~512 tokens, 10–20% overlap" and says overlap "insures against" boundary splits: good for the interview item, but our model answer must add the F ≤ O + 1 limit and the unit question.

**External sources** (opened 2026-10-17 unless marked):

| # | Source | Type | Status |
|---|---|---|---|
| [C2-1] | LangChain `langchain_text_splitters` source, `base.py` and `character.py` (master), https://github.com/langchain-ai/langchain/tree/master/libs/text-splitters/langchain_text_splitters ; issue #29884 "TokenTextSplitter start indices are sometimes -1", https://github.com/langchain-ai/langchain/issues/29884 ; PR #31222 (closed unmerged), https://github.com/langchain-ai/langchain/pull/31222 ; issue #20908 (`keep_separator` start/end), https://github.com/langchain-ai/langchain/issues/20908 | Source code, issue tracker | verified |
| [C2-2] | LlamaIndex `SentenceSplitter` source (`node_parser/text/sentence.py`, `constants.py`, `utils.py`, `settings.py`, main), https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/node_parser/text/sentence.py | Source code (reading only) | verified |
| [C2-3] | Cohere docs: Models (https://docs.cohere.com/docs/models), Embed v2 reference (https://docs.cohere.com/reference/embed), Tokens and tokenizers (https://docs.cohere.com/docs/tokens-and-tokenizers) | Official docs | verified; embed-v4.0 local tokenizer availability **UNVERIFIED** |
| [C2-4] | Smith & Troynikov, "Evaluating Chunking Strategies for Retrieval", Chroma technical report, 2024-07-03, https://www.trychroma.com/research/evaluating-chunking (= Source C #26) | Technical report | verified |
| [C2-5] | `chunking_evaluation` code for [C2-4], https://github.com/brandonstarxel/chunking_evaluation (= C#27) | Code (MIT) | verified (repo page only; not run) |
| [C2-6] | S. Han, "Finding the Best Chunking Strategy for Accurate AI Responses", NVIDIA Technical Blog, 2025-06-18, https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/ (= C#28) | Vendor blog | verified |
| [C2-7] | Bhat, Rudat, Spiekermann, Flores-Herr, "Rethinking Chunk Size For Long-Document Retrieval: A Multi-Dataset Analysis", arXiv 2505.21700 v2, 2025-05-29, https://arxiv.org/abs/2505.21700 | Paper (preprint) | verified (abstract + HTML v2) |
| [C2-8] | Bennani & Moslonka, "A Systematic Analysis of Chunking Strategies for Reliable Question Answering", arXiv 2601.14123 v1, 2026-01-20, https://arxiv.org/abs/2601.14123 | 3-page preprint | verified (abstract + HTML) |
| [C2-9] | Schwaber-Cohen & Patel, "Chunking Strategies for LLM Applications", Pinecone, 2025-06-28, https://www.pinecone.io/learn/chunking-strategies/ (= C#29) | Vendor guide | verified |
| — | sentence-transformers 6.1.0 installed source (`base/modules/transformer.py` L743, L866–L867) and the cached MiniLM `sentence_bert_config.json` (max_seq_length 256, snapshots `1110a243…` and `c9745ed1…`) | Local, read-only | verified by reading; special-token counting **UNVERIFIED** (not run) |
| — | PyPI JSON for langchain-text-splitters, llama-index-core, hypothesis, tiktoken, tokenizers, chonkie, semchunk | Package index | verified 2026-10-17 |

Nine external sources, slightly over the cap of about 6, because the card names three (C#26, #27, #29) and the research note asks for library source plus primary studies.

**Scratch measurement made in this session** (local and offline; no API): the 07 H.1 `recursive_chunks` code, executed from the lesson text, on PyMuPDF 1.26.7 pages of Corpus D, counted with the cached MiniLM `tokenizer.json` (with [CLS]/[SEP]) and tiktoken `cl100k_base`. Results: 72,593 characters; 6.21 characters per WordPiece token, 5.57 per cl100k token; per-page 1000/200 gives 97 chunks with WordPiece lengths 59 / 149 / 182 and none over 256; 1500/300 gives 65 chunks, 4 over 256; 2000/400 gives 65 chunks, 32 over 256 and 6 tail chunks under a quarter of the size; 500/100 gives 201 chunks. **These reproduce 07 D.6 exactly on PyMuPDF text**, which closes one of 07's UNVERIFIED items. Script: `scratchpad/C2_work/measure_tokens.py` (not in the project).


### 2. Gap audit

"Studied" comes from `progress/concept_tracker.csv`: P1 is `exposed` (O1 diagnostic only; MC-001 open), P4, P6, C1, C3, M1 and I1 are `not_started`. "Written" never counts as studied.

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | **A token is what the model's tokenizer produces**, not a character; the embedder only maps token ids to vectors | 02 outcome "explain chars vs tokens"; every size number; MC-001 | 07 D.5 shows counts, but never says what a tokenizer does (BPE vs WordPiece) | P1 | no (exposed; **MC-001 open**) | bridge | Short §2: one picture (text → tokenizer → ids → embedder), one measured example (v0 chunks: median 935 characters and median 149 WordPiece tokens, both measured; the "1,000 = 1,000 tokens" belief overstates by about 6×). Flag MC-001 |
| 2 | **Characters per token is corpus- and tokenizer-specific** (6.21 WordPiece, 5.57 cl100k on Corpus D; folk "4 chars/token" wrong here) | D.5, J3, sizing | taught (07 D.5) | C2 (measured) | no | core | Keep; add "measure it on every new corpus" as a tool check |
| 3 | **Embedder input cap and silent truncation**: MiniLM 256 WordPiece tokens (first tokens kept); bge-small 512; Cohere `embed-v4.0` 128k context with `truncate=END` default, `embed-english-v3.0` 512 | D.6, J1, PK-3, 02 outcome "compute token lengths" | taught for MiniLM/bge; **Cohere row missing** (06 §3.2 still says UNVERIFIED) | P4 | no | bridge | Short: the cap table with the Cohere row from [C2-3]; say plainly that v0's default embedder cannot truncate a 1,000-char chunk, so the cap matters for the MiniLM fallback and for large I1 sizes |
| 4 | **One vector per chunk (pooling) → dilution** | B.2, D.7, PK-5 | taught as a toy (D.7) | P4 | no | bridge | Keep the toy; one sentence on mean/CLS pooling |
| 5 | **Fixed windows**: stride S − O, count ceil((L − O)/(S − O)), storage → S/(S − O) | D.2, C2-R-01, lab Task 2 | taught | C2 | no | core | Keep (formula sheet) |
| 6 | **Containment**: P = min(1, (S − F + 1)/(S − O)); guaranteed iff F ≤ O + 1 | D.3, PK-4, C2-R-02, lab Task 4 | taught | C2 | no | core | Keep; contrast with the book's "nothing lost at the seams" |
| 7 | **Recursive splitter, exact rules**: the separator is the first one found *anywhere* in the text; pieces `< chunk_size` (strict) are kept; longer pieces recurse with the remaining separators; with no separator left a piece is emitted **whole and can exceed `chunk_size`** (only `""` prevents this); `keep_separator=True` = attach to the *start*, `"end"` also exists | D.4, lab Task 5, LLMOps comparison | **incomplete**: 07 D.4 says "no piece ever exceeds chunk_size" without the condition; `"end"` option and the strict `<` not mentioned | C2 | no | core | Full: a 6-line pseudo-code of `_split_text` + `_merge_splits` from [C2-1]; Short: the two-phase picture and "actual overlap ≤ requested, whole pieces" |
| 8 | **Overlap is in the same unit as `length_function`** (chars with `len`, tokens with `from_tiktoken_encoder`); a token budget is summed over pieces, so it is approximate | 02 failure "overlap set in the wrong unit"; D.5 | **incomplete**: D.5 covers size units, not overlap units or the summing approximation | C2 | no | core | Short: one line; Full: why the merge sums piece lengths (token count of a join ≠ sum) |
| 9 | **Offsets that map back exactly**: half-open spans, document offsets as the one coordinate system, `page_segments` as a derived view, the round-trip test `doc[a:b] == text` | D.9, H.1, H.3, lab Tasks 3, 6, 7; Gate 2→3 | taught | C2 (C3 consumes) | no | core | Keep; make the round-trip test the lesson's centre |
| 10 | **`add_start_index` is a search, not a record**: `text.find(chunk, prev_start + prev_len − chunk_overlap)`; wrong or −1 when overlap is in tokens (issue #29884, open), when text repeats (boilerplate), or when a tokenizer decode changes the text | H.2 uses it; LLMOps comparison | **missing** | C2 | no | core | Full (plus one Short warning): why our chunker *produces* offsets instead of searching for them; verify cell shows the failure |
| 11 | **Token-based splitters**: `from_tiktoken_encoder` (character splitting, merge measured in gpt2 tokens) vs `TokenTextSplitter` (exact token windows, each decoded separately: can cut words and multibyte characters, no offsets) | D.5 table, repo cells (`reliable_rag` 6, `proposition_chunking` 9) | **incomplete**: named, mechanism not taught | C2 | no | core (Full) | Full: a two-row comparison; the bridge to P1 tokenizers |
| 12 | **Per-page vs cross-page scope**, page-break cuts (8 mid-sentence, 16 orphaned headings on PyPDFLoader text), citation trade-off | B.1, D.8, J5, lab Task 6 | taught; PyMuPDF counts of cuts/headings not re-measured | C2 / C1 | no | core | Keep; re-measure the 8/16 counts on PyMuPDF in the verify notebook |
| 13 | **Clean before you chunk, never after**: the book cleans each chunk *after* splitting (Ch1 p.5/14, p.7/14); any edit after chunking breaks the offset round-trip; v0 cleans nothing and records a snapshot | G.1, C1 | **missing** as a rule | C1 | no | bridge | One line in Short with the book page; link C1 snapshot |
| 14 | **Chunk length distribution**: tiny tail chunks at page ends (6 under 25% of S at 2000/400 per page), mean vs max | apply-it tool; I1 | **missing** | C2 | no | core | Short: one histogram (WordPiece lengths with the 256 line) |
| 15 | **`params_hash` and deterministic chunk ids** (what goes into the hash: name, unit, size, overlap, separators, scope; tokenizer id when unit = tokens) | H.3, lab Task 7, Gate 2→3 "identical params_hash" | taught, but **two recipes** (06 block → `1ca9c5a3b548`; 07 `ChunkerConfig` → different) | C2 → C3 | no | core | Teach the 06 recipe only; mark 07 H.3's as superseded (see §4) |
| 16 | **Gold evidence as character spans, not chunk ids**; a boundary cut through a gold span | 02 outcome "diagnose a boundary cut through a gold span"; C2-R-04; J8 | taught (E, J8) | M1 | no | bridge | Short: the PPP sentence as the worked boundary diagnosis |
| 17 | **Hit@k / CE@k in one line** (used in B.1, J1, J5) | B.1 analysis, J items | used, defined only in passing | P6 / M2 | no | bridge | One sentence each where first used; link P6 |
| 18 | **Fixed k vs equal token budget** (changing size changes context tokens) | PK-6, J10, every external study | taught in I (I1) | I1 | no | next (+1 bridge line) | One line plus link; the grid itself stays in I1 |
| 19 | **What the evidence says about size and overlap** (no universal best; fixed-k confound; overlap rarely measured well) | lesson "Full"; interview | **missing** (07 lists Source C as reading only) | C2 summary / I1 runs | no | core (Full) | Full: §5 table in study → result → limits → meaning form |
| 20 | **Recursive vs fixed vs sentence/structure/semantic** names and when each is tried | interview Q4; K | taught as a table (E, K) | I2/I3/I4/I-CMP | no | next | Link only; keep the one-line table |
| 21 | **Context window (X1) vs overlap** (query time vs index time; MC-003 is a related stage mix-up) | E table, C2-T-01 | taught | X1 | no | next | Keep the contrast row; flag MC-003 |
| 22 | **Repeated boilerplate** (footers) and its two effects: similar vectors and wrong `find()` offsets | J4 | taught (J4) without the offset effect | C1 | no | bridge | Add the offset effect to J4 |


### 3. Quiz coverage

**No `study/questions/C2_questions.md` exists.** 07 Part L has 16 items (C2-R-01…05, C2-A-01…06, C2-T-01…05) plus the M.2 prompts, written for the full A–M lesson. Two problems if they are copied into the kit as they are:
- **Short mode cannot answer them yet.** There is no Short version. C2-R-01/R-02 need the D.2–D.3 derivations, C2-A-03 needs the LangChain separator rule (D.4), C2-A-06 needs D.6's WordPiece vs cl100k counts. The blueprint (§6) puts each of these into Short.
- **Gaps in the items themselves.** No item tests: overlap measured in the wrong unit (the 02 failure line), `add_start_index` offsets, the Cohere cap (v0's real embedder), cleaning after chunking, or tail chunks. C2-T-03…05 are practice scenarios that already appear in the lesson, so CR-13 needs fresh ones (the hidden seed-bank reserve for C2 must stay out of the kit).

**Needed question titles** (FORMAT.md ids; every key point must be answerable from Short):

| Id | Type / set | Title |
|---|---|---|
| C2-PRE-01 | R / pre | "Your splitter says chunk_size=1000. How many tokens is one chunk?" (MC-001 probe) |
| C2-PRE-02 | R / pre | "Does a 200-character overlap stop any sentence being cut in two?" |
| C2-PRE-03 | R / pre | "What happens to text past an embedding model's input limit?" |
| C2-R-01 | R / main | Count fixed windows and the storage multiplier (from 07 C2-R-01) |
| C2-R-02 | R / main | The containment bound F ≤ O + 1 and P(contained) (07 C2-R-02) |
| C2-R-03 | R / main | Name the unit of `chunk_size` **and of `chunk_overlap`** in four code paths (07 C2-R-03, extended to overlap) |
| C2-R-04 | R / main | Why gold evidence is stored as spans (07 C2-R-04) |
| C2-R-05 | R / main | What MiniLM, bge-small and Cohere `embed-v4.0` each do with a 300-token chunk (07 C2-R-05 plus the Cohere row) |
| C2-A-01 | A / main | Trace `fixed_window_chunks` on a 23-character string (07 C2-A-01) |
| C2-A-02 | A / main | Trace the recursive splitter on "the cat sat on the mat", ours vs LangChain (07 C2-A-03) |
| C2-A-03 | A / main | Diagnose a boundary cut through a gold span: the PPP sentence across pages 12→13 (02 outcome) |
| C2-A-04 | A / main | `from_tiktoken_encoder(chunk_size=200, chunk_overlap=50)` with `add_start_index=True` gives `start_index = -1`. Why? (new; [C2-1]) |
| C2-A-05 | A / main | A teammate counts with cl100k and finds 18 chunks over 256 (07 C2-A-06) |
| C2-A-06 | A / review | Page-relative vs document offsets: CE@4 is zero except on page 1 (07 C2-A-05) |
| C2-T-01 | T / main | Overlap vs a context window (07 C2-T-01) |
| C2-T-02 | T / main | Choose the size and unit for a new corpus with a 512-token embedder; say what you measure first (new scenario, not in the lesson) |
| C2-R-06 | R / interview | AIQ `04-rag-and-retrieval/questions.md` Q5, "How do chunk size and overlap affect retrieval quality, and what numbers would you start with?" (`source=AIQ-04-Q5`, MIT notice). Our answer adds the unit, the F ≤ O + 1 limit and the fixed-k confound |

FORMAT.md allows at most 2 external items per concept; only C2-R-06 is external.


### 4. Errors found in existing material (not edited)

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| C2-E1 | 06 §3.2 Cohere row; 06 §2.4 `model_id` comment ("input limit UNVERIFIED") | Still says the Cohere input limit is UNVERIFIED | Cohere Models page: `embed-v4.0` context 128k; Embed reference: `truncate` default `END`, max 96 texts per call ([C2-3]); Foundation §6.2 has the same facts | Fill the row (128k; END; 96) and close E-3 for the limit. At 1,000 characters truncation cannot happen with this model. Record `truncate` explicitly in the embed config (Foundation E2) |
| C2-E2 | 07 D.4 step 1 ("so no piece ever exceeds `chunk_size`") | True only while `""` is the last separator. With custom separators that omit `""`, `_split_text` appends an over-long piece whole | `character.py` `_split_text`: when no separators remain, the piece is appended as it is ([C2-1]) | Add the condition. Also note the strict `<` test and that `keep_separator` accepts `"start"`/`"end"` |
| C2-E3 | 07 H.1 `DEFAULT_SEPARATORS` vs 06 §2.4 `separators` | 07 omits `""`; 06 lists it. Feeding `""` to H.1's `_split_spans` would never advance | Already recorded in C2LAB_FACTS §2 #1; not yet fixed in 07 | Note in 07 H.1 that `""` is handled by the "no separators left" branch |
| C2-E4 | 07 H.3 `ChunkerConfig.params_hash()` vs 06 §2.4 recipe; `sources/verification/C3/c3_measure.py` | Several different `params_hash` values for "v0" in course files: `1ca9c5a3b548` (06 block, the lab); `77bc4c45809b` / `12eafa2247a1` / `0ad9b961bc23` (07 dict variants); C3 uses a fixed-window chunker, `db1d77b74d1f` | C2LAB_FACTS §2 #4 and its interlock note | One recipe for the course (the 06 block, as the lab does); mark 07 H.3's as superseded; align C3. Gate 2→3 ("identical params_hash") depends on it |
| C2-E5 | 07 D.8 Assumption, D.6, Verification log ("PyMuPDF chunk counts UNVERIFIED"); 06 §3.2 ("PyPDFLoader text") | Now measured on PyMuPDF 1.26.7: 97 / 65 / 65 chunks; WordPiece 59/149/182, 109/215/270, 59/160/365; over 256: 0 / 4 / 32. **Identical** to the PyPDFLoader numbers | Scratch measurement in §1 (to be re-run in the verify notebook) | Drop the UNVERIFIED label once the verify notebook confirms it. Keep the 8 mid-sentence cuts and 16 orphaned headings as PyPDFLoader-only until re-measured |
| C2-E6 | 07 G.2, H.2 (the trace uses `add_start_index=True`) | Never warns that `start_index` is found by `text.find` from a guessed position | `base.py` `create_documents`; issue #29884 open; PR #31222 closed unmerged ([C2-1]) | Add a J item: with overlap in tokens the guess lands past the true start (−1 or a later match); repeated text can match the wrong place. Our chunker records offsets instead of searching |
| C2-E7 | 02 card C2, "Book" line | Omits Ch1 p.7/14 (algorithm sketch with ~1000/~200 and "clean each chunk"), which 04 cites, and App p.16/23 (glossary "Fixed-Size Chunking") | Book extract | Add both pages |
| C2-E8 | 02 card C2, "Repo" line; 04 C2 row | `context_enrichment_window_around_chunk.ipynb` cell 13 is described only as "cuts mid-word". It also has no `0 <= overlap < size` check (overlap ≥ size never ends or moves backwards), no stop when a window reaches the end (redundant tail chunks, the C2-A-04 bug), and it stores the whole document in every chunk's metadata | Cell 13 source | Add these to the card; it is a ready-made debugging exercise |
| C2-E9 | 08 L199 | 08 says the book describes the splitter "as plain character slicing" (Ch1). Ch1 only says "about 1,000 characters"; the "character counter" wording is in Ch8 p.2/11 | Book extract | Cite Ch8 p.2/11 for that wording |
| C2-E10 | `reliable_rag.ipynb` cell 6 (not flagged in 04/08) | Sizes chunks as 500 **gpt2** tokens for `embed-english-v3.0`, whose context is 512 **Cohere** tokens: a unit mismatch right at the cap. Whether any chunk is truncated is **UNVERIFIED** (Cohere tokenizer not run) | Cell 6; [C2-3] Models page | Use it in C2 as the reading example of "count with the embedder's tokenizer" |
| C2-E11 | 06 §2.4 MiniLM `revision: 1110a243…` | The local HF cache holds a second snapshot (`c9745ed1…`). A loader that does not pass `revision=` may load the other one | `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/` | Always pass `revision`; the tool and notebooks record it |
| C2-E12 | Book Ch1 p.4/14, p.13/14, App p.14/23 | Overlap said to ensure no information is lost | 07 D.3 derivation; the book's own Ch8 p.1/11 | Already handled in 07; keep |
| C2-E13 | `proposition_chunking.ipynb` cell 9, `reliable_rag.ipynb` cell 6 | Import from `langchain.text_splitter`, the pre-1.0 path. Whether it still resolves under langchain 1.x is **UNVERIFIED** | Cells 6 and 9 | Reading only; the LLMOps notebook imports `langchain_text_splitters` |


### 5. What the research says

#### 5.1 How the libraries really chunk (primary: source code)

**[C2-1] LangChain `RecursiveCharacterTextSplitter`** (`langchain-text-splitters`, master; newest release 1.1.3, 2026-10-02).
- **Defaults:** `chunk_size=4000`, `chunk_overlap=200`, `length_function=len` (characters), `keep_separator=True` (recursive class only; the base class default is `False`), `add_start_index=False`, `strip_whitespace=True`, separators `["\n\n", "\n", " ", ""]`.
- **Validation:** `chunk_size <= 0`, `chunk_overlap < 0` and `chunk_overlap > chunk_size` raise `ValueError`; `chunk_overlap == chunk_size` is accepted.
- **Split:** the separator is the *first one in the list that occurs anywhere in the text*. Pieces shorter than `chunk_size` (strict `<`) are kept; longer pieces recurse with the remaining separators. If none remain, the long piece is appended whole, so a chunk can exceed `chunk_size` when `""` is not in the list. `keep_separator=True` attaches the separator to the start of the next piece; `"end"` attaches it to the end (added in 2024, issue #20908).
- **Merge:** add pieces while `sum(length_function(piece))` stays within `chunk_size`. On overflow, emit, then drop pieces from the front while the remainder is above `chunk_overlap` or the next piece still would not fit. So the real overlap is made of whole pieces, is **≤ `chunk_overlap`**, and can be **0** when the last piece is longer than the overlap. With a token length function the bound is approximate: the token count of joined text is not exactly the sum of the pieces' counts.
- **`add_start_index`:** not a record of where the chunk came from. It guesses `offset = previous_start + previous_length − chunk_overlap` and runs `text.find(chunk, offset)`. With `from_tiktoken_encoder` or `TokenTextSplitter`, `chunk_overlap` is in tokens but is subtracted from a character position, so the search starts past the true start and returns −1 or a later duplicate. Issue #29884 (opened 2025-02-19, labelled Bug 2026-06-15) is **still open**; the fix PR #31222 was closed unmerged because decoded token windows do not always reproduce the source text (an Aug 2026 comment adds that windows can split multibyte UTF-8 characters). With character units the guess is usually safe, but repeated text (footers, boilerplate) can still match the wrong place.
- **`from_tiktoken_encoder`** keeps the character splitter and only measures pieces in tokens (default `gpt2`). **`TokenTextSplitter`** cuts exact token windows (stride `chunk_size − chunk_overlap`) and decodes each window separately: it can cut words and characters and keeps no offsets.
- **What it means for the project:** the course chunker must *produce* offsets during splitting and test them with the round-trip assert. Never trust `start_index` for gold-span matching. The LLMOps notebook shows both behaviours side by side.

**[C2-2] LlamaIndex `SentenceSplitter`** (reading only; `llama-index-core` 0.14.25).
- Defaults `chunk_size=1024` and `chunk_overlap=200`, both in **tokens** of `tiktoken.encoding_for_model("gpt-3.5-turbo")`, i.e. `cl100k_base`. (A different constant, `DEFAULT_CHUNK_OVERLAP = 20`, also exists: two "default overlaps" in one package.)
- Split order: paragraph separator `"\n\n\n"` → NLTK punkt sentences → a punctuation regex → spaces. It prefers whole sentences and carries whole trailing splits as overlap.
- **Hidden effect:** `split_text_metadata_aware` subtracts the token length of the node's metadata string from `chunk_size`, so with metadata the chunk text is shorter than the number you set. It raises when the metadata is longer than the chunk size.
- **For the project:** a third meaning of "chunk_size = 1024" (cl100k tokens minus metadata). Teach it in Full as a unit trap; do not install LlamaIndex.

**[C2-3] Cohere embed limits.** `embed-v4.0`: context 128k tokens, output 256/512/1,024/1,536 dimensions. `embed-english-v3.0`: 512 tokens. The v2 Embed API takes at most 96 texts per call; `truncate` is `NONE | START | END` with default `END` (the end is dropped silently; `NONE` returns an error instead); an optional `max_tokens` truncates further. Cohere tokenizers can run locally after downloading the model's `tokenizer_url` from the Models API; whether `embed-v4.0` publishes one is **UNVERIFIED**.
- **For the project:** with the default embedder, a 1,000-character chunk is far below the cap, so truncation is a **fallback-model** problem (MiniLM 256) and an I1 problem at large sizes. Set `truncate="NONE"` in the embed call, so an over-long input fails loudly instead of being cut (a decision for C3; it costs nothing at v0 sizes).

**sentence-transformers 6.1.0** (installed source): `max_seq_length` is handed to the tokenizer as `model_max_length` (`transformer.py` L866–L867). Whether `[CLS]`/`[SEP]` count inside the 256 is **UNVERIFIED** here; the verify notebook checks it with one call to `model.tokenize`.

#### 5.2 What studies say about size and overlap

| Study | What was tested | Result | Limits | What it means for us |
|---|---|---|---|---|
| **[C2-4] Chroma 2024** (Smith & Troynikov) | 5 corpora (328k cl100k tokens), 472 LLM-written queries with exact excerpts; token-level recall, precision and IoU; LangChain recursive and token splitters, Kamradt semantic, cluster and LLM chunkers; **sizes and overlaps in cl100k tokens**; k = 5 (fixed); text-embedding-3-large, plus MiniLM | Recall stayed in a narrow band (about 84–92%). Recursive 400/0 reached 89.5 recall and IoU 3.6, against 88.1 and 3.3 at 400/200. The OpenAI Assistants default, 800/400 tokens, gave 87.9 recall and the lowest IoU (1.4). The best IoU was the cluster chunker at 200 (8.0). With MiniLM, overlap raised recall for the token splitter (250/125: 82.4 vs 250/0: 77.1) | k fixed, so larger chunks also send more tokens (IoU punishes this by design); standard deviations of about 30 points with no paired test; LLM-written queries; only generated excerpts count as relevant | **The closest analogue to our span gold** (token spans, not chunk ids). Overlap's effect on recall is small and model-dependent; its cost (duplication) is certain. Supports measuring at equal budget (I1) |
| **[C2-6] NVIDIA 2025** (vendor) | 5 datasets; token chunks 128–2,048 with 15% overlap (overlap chosen on one dataset), page-level and section-level chunks; fixed reranker; k = 10; generator Nemotron-70B; **answer accuracy judged by two LLMs**; no retrieval metric | Page-level had the best average (0.648, std 0.107); token sizes 0.603–0.645; the best size differed per dataset (512, 1,024 or page); 128 and 2,048 were usually worst | Answer-only judged metric; fixed k; no confidence intervals; one internal dataset; vendor models | Per-page units are a strong, citation-friendly baseline, which supports v0's per-page scope. The spread between sizes is small next to the dataset effect |
| **[C2-7] Bhat et al. 2025** (arXiv 2505.21700) | 6 QA datasets (4 stitched into long synthetic documents); 64–1,024-token chunks, **no overlap**; two long-context embedders (Stella 1.5B, Snowflake arctic-l v2); Recall@1–5; gold = the chunk contains the answer string | Short factoid sets peak at 64 tokens (SQuAD R@1 0.64); broad sets at 512–1,024; **the two embedders disagree** on the best size for the same dataset (COVID-QA: 64 vs 1,024) | String-match gold favours bigger chunks at fixed k; synthetic stitched documents; text and tables disagree in places | The best size depends on the question type **and** the embedder, so an I1 result never transfers across a model change |
| **[C2-8] Bennani & Moslonka 2026** (arXiv 2601.14123, 3-page preprint) | Natural Questions; SPLADE (sparse) retriever; Mistral-8B; token/sentence/semantic/code chunkers; sizes 50–500; overlap 0% vs 20%; BERTScore and EM with bootstrap CIs | No measurable overlap benefit (|Δ| ≤ 0.004 BERTScore, ≤ 0.001 EM) at extra indexing cost; sentence chunking cost-effective; quality falls past about 2.5k context tokens | Answer metrics only; one dataset and model; sparse retriever; the text is inconsistent about the overlap values | Weak but consistent with Chroma: overlap is not a free win. In C2 it is taught as a probability bound, not a quality claim |
| **[C2-9] Pinecone 2025** (vendor guide) | Survey; no measurements | Advises fixed sizes near the embedder's window and warns that tokenizers differ between models | No evidence; ignores dilution and MiniLM's 128-token training length | Use only for vocabulary. Its "size near the model maximum" advice is the opposite of what the dilution toy and the studies suggest |

**Current practice (2024–2026), across these sources.** Recursive splitting in tokens is the common default (AIQ Q5 says about 512 tokens with 10–20% overlap; Chroma tested 200–800). Sizes are stated in **tokens** in most tools and papers but in **characters** in the book and the repo's `encode_pdf`, so a "1,000" from the book is roughly 160–180 tokens on our corpus, at the small end of what papers test. Structure-, sentence- and page-level units are the main alternatives (I2, I-CMP).

**Pitfalls with evidence.** (1) Unit confusion between size, overlap and the embedder cap (repo cells; MC-001). (2) Silent truncation at the cap (MiniLM: 4 of 65 chunks at 1500/300, 32 of 65 at 2000/400, measured). (3) Offsets found by search are wrong in token mode (issue #29884). (4) Overlap that cannot cross a per-page boundary (07 D.8). (5) Chunk ids used as gold (AIQ also warns, `04` L1192). (6) Comparing sizes at fixed k (every study above).

**How to evaluate chunking.** Retrieval first, with span gold: CE@k as primary, Span-Coverage@k and Hit@k/MRR as diagnostics, at fixed k **and** at equal context-token budget (I1). Answer quality separately, on the top configurations only. In C2 itself there is no retrieval metric yet: C2 measures **chunk properties** (counts, length distributions in the embedder's tokens, truncation rate, real overlap, boundary cuts through gold spans and sentences, round-trip and determinism).

**Interview questions** (AIQ first):
1. AIQ 04 Q5: "How do chunk size and overlap affect retrieval quality, and what numbers would you start with?" (MIT; used as C2-R-06).
2. AIQ 04 Q4: "What chunking strategies do you know, and how do you pick one?" (link to I-CMP; not a C2 item).
3. AIQ 04 Q4 follow-up: "How do you A/B test two chunking strategies?" (equal budget; spans not ids).
4. Derived: "Your chunk_size is 512. Is that characters or tokens, and does it fit your embedder?"
5. Derived (AIQ 04 L1194): "A chunking change invalidated all chunk-id labels. What should the gold set have stored?"


### 6. Lesson blueprint

The new HTML lesson (`study/lessons/C2_chunking.html`, Short/Full) **re-presents** 07 Parts A–H, J–M in the P3 order. 07 stays the full reference; its Part I moves to the I1 lesson and is only linked.

**The answer first (draft, 5 sentences).**
1. Chunking cuts each document into pieces that are embedded and retrieved one at a time; it decides what a single vector stands for.
2. Every size is a number **in a unit** (characters, the embedder's tokens, or words), and v0 uses 1,000 characters with 200 overlap, which is about 150–180 tokens on our corpus, not 1,000.
3. Overlap guarantees that a fact stays whole only if it is at most O + 1 characters long, and never across a page when you split page by page.
4. Each chunk must carry exact document offsets, so that `doc[start:end] == text` holds and gold spans can be matched to any chunking.
5. Check every chunk against the embedder's own token limit, because text past the limit is dropped silently; the best size is then found by measurement in I1, not by a rule.

**The theory in one read** (11 linked ideas):

| # | Idea | Formula or rule |
|---|---|---|
| 1 | A chunk is a half-open span of one snapshot's text | `chunk = doc[a:b]`, `0 ≤ a < b ≤ L` |
| 2 | Units: chars, the embedder's tokens, words | `tokens ≈ chars / r`, r measured per corpus and tokenizer (6.21 WordPiece, 5.57 cl100k on Corpus D) |
| 3 | Fixed windows | stride `s = S − O`; `n = ceil((L − O)/s)` for L > S; storage → `S/(S − O)` |
| 4 | Containment | `P = min(1, (S − F + 1)/(S − O))`; guaranteed iff `F ≤ O + 1` |
| 5 | Recursive splitting | split on the first separator present; recurse on pieces `≥ S`; merge greedily; real overlap ≤ O, whole pieces |
| 6 | Overlap shares the size's unit | `length_function` decides both |
| 7 | Scope | per page: no chunk crosses a page, overlap stops at page ends; cross page: `page_segments` record each page touched |
| 8 | Offsets are produced, never searched | round trip `doc[a:b] == text`; `find()`-based `start_index` can be wrong |
| 9 | The embedder cap | `truncated = tokens_embedder(text) > max_seq_length` (MiniLM 256; Cohere v4 128k) |
| 10 | Dilution vs fragmentation | one pooled vector per chunk; toy `cos = 1/√(1 + n²)` |
| 11 | Identity | `params_hash = sha256(json(chunking_block, sort_keys))[:12]`; `chunk_id = doc:snapshot:params_hash:seq` |

**Formula-sheet items:** stride; the window count; the storage multiplier; P(contained) and F ≤ O + 1; chars per token r; the truncation test; the toy cosine; the `params_hash` and `chunk_id` recipes; "real overlap ≤ requested".

**Step-by-step outline (running example: Corpus D, the climate PDF, PyMuPDF text).**
1. The problem: the PPP sentence cut at pages 12→13; no per-page chunk holds it (07 B.1).
2. Bridge to P1: the same chunk measured three ways (characters, WordPiece, cl100k); MC-001 named.
3. Fixed windows by hand on the 23-character string, then the formula (07 D.2, C2-A-01).
4. Overlap as probability: P(contained) for F = 500 at O = 0/200/400 (0.501/0.626/0.835); the F ≤ O + 1 rule; the book's claim checked (Ch1 p.4/14 vs Ch8 p.1/11).
5. The recursive splitter: "the cat sat on the mat", ours vs LangChain (07 C2-A-03); the separator rule; real overlaps 182/142/199/179 on Corpus D (lab Task 8).
6. Scope: per page (97 chunks) vs cross page (92 chunks, 41 crossing a page) on PyMuPDF text; the citation trade-off.
7. Offsets: half-open spans, document coordinates, `page_segments`; the round-trip test; why `start_index` is not enough.
8. The cap: token lengths of the 97 v0 chunks under MiniLM (max 182 of 256); at 1500/300, 4 over; at 2000/400, 32 over; the Cohere row (128k).
9. Dilution vs fragmentation: the toy (D.7) and the page-1 chunk (B.2).
10. Identity: `params_hash` = `1ca9c5a3b548` and the 97 ids; change the overlap to 199 and every id changes (lab Task 7).
11. What the evidence says: the §5.2 table in four lines; the size grid belongs to I1.
12. Apply: run the chunk-fit tool on your own document.

**Visuals that earn their place** (hand-drawn SVG unless marked):

| Visual | The one thing it shows |
|---|---|
| Ruler strip: one 1,000-char chunk shown against three rulers (chars, WordPiece, cl100k) | The same text is 1,000, about 160 or about 180 "units" (fixes MC-001) |
| Sliding windows on a strip, with a fact bar that slides (interactive, S/O/F sliders) | Containment happens when the fact's offset r ≤ S − F; the probability is the green share |
| P(contained) vs F for O = 0, 200, 400 (Plotly in the verify notebook; SVG in the lesson) | The curve is flat at 1 up to O + 1, then falls linearly |
| Split → merge diagram for the recursive splitter | Overlap is whole trailing pieces, so it is ≤ O |
| Two page panels with the PPP sentence across the break, per-page vs cross-page chunks | Overlap cannot rescue a page cut |
| Histogram of WordPiece lengths of the v0 chunks, with the 256 line, plus 1500/300 and 2000/400 | Truncation appears only above 1,500 characters for MiniLM |
| A chunk record card (fields → which failure each prevents) | Provenance fields are tools, not paperwork |

**Full-only details:** the derivations of the count and P(contained); LangChain's `_split_text` / `_merge_splits` in 8 lines of pseudo-code; `keep_separator` start/end; the strict `<`; the "`""` missing → over-long piece" case; `add_start_index` mechanics and issue #29884; `from_tiktoken_encoder` vs `TokenTextSplitter`; LlamaIndex's metadata-aware size; the Cohere `truncate` options; the dilution toy's maths; the §5.2 studies with their limits; the `params_hash` recipe conflict history; the repo's four units (07 G.5).


### 7. Verify notebook plan

`study/notebooks/C2_chunking_verify.ipynb`. Plain Python plus numpy, PyMuPDF, `tokenizers`/`transformers` (MiniLM and bge tokenizer files from the HF cache), tiktoken and Plotly. **No API call, no LLM, no framework.** Runs offline with `HF_HUB_OFFLINE=1`; the chunker is imported from the C2 lab's reference module (or 07 H.1), never re-typed. Estimated runtime under 30 s on CPU (one MiniLM load of a few seconds; everything else is string work).

| # | Recomputes | Data | Expected (source) |
|---|---|---|---|
| 1 | Window count formula vs brute force for L = S+1 … 20S, four (S, O) settings; storage ratio → S/(S − O) | synthetic | 0 mismatches; 1.247 at L = 73,536 (07 D.2) |
| 2 | P(contained): formula vs brute force; Plotly curve P vs F for O = 0/200/400, S = 1000 | synthetic | 0.501 / 0.626 / 0.835 at F = 500; 1.0 up to F = 201 (07 D.3, lab Task 4) |
| 3 | Recursive splitter traces ("the cat sat on the mat"; Part F paragraph 300/60) | 07 fixtures | (0,8)(4,12)(8,15)(12,22); [0,294)[238,534)[478,773)[714,785) (lab Task 5) |
| 4 | Corpus D per page vs cross page, 1000/200: counts, lengths, crossings | PyMuPDF pages | 97 vs 92 chunks; 41 cross a page; lengths 393/935/1000 (C2LAB_FACTS) |
| 5 | Real overlap distribution on the 64 same-page pairs (histogram) | Corpus D | min/median/max 109/177/200 (lab Task 8) |
| 6 | Characters per token, three tokenizers | Corpus D | WordPiece 6.21, cl100k 5.57 (this session); gpt2 to be measured (07 had 5.07 on PyPDFLoader) |
| 7 | WordPiece length distribution and truncation count at 500/100, 1000/200, 1500/300, 2000/400 (Plotly histogram with the 256 and 512 lines) | Corpus D | 201 / 97 / 65 / 65 chunks; over 256: 0 / 0 / 4 / 32 (this session; matches 07 D.6) |
| 8 | Runtime truncation check: `SentenceTransformer(all-MiniLM-L6-v2, revision=1110a243…)`, `model.tokenize([long_text])` length, and the embedding of a 300-token text equals that of its first 256 tokens | local model | answers the 07 UNVERIFIED item on `[CLS]`/`[SEP]` counting (expected: input length 256 including specials; cosine 1.0 between the two vectors) |
| 9 | Page-break census on PyMuPDF text: pages not ending in terminal punctuation, mid-sentence cuts, orphaned headings | Corpus D | re-measures 07 D.8's 24 / 8 / 16 (PyPDFLoader) on the v0 extractor |
| 10 | Offset round trip and `page_segments` decoding for all 97 records; `params_hash` = `1ca9c5a3b548`; `chunks.jsonl` sha256 | lab output | `d4108b89…011b` (C2LAB_FACTS) |
| 11 | A find-based `start_index` re-implementation (8 lines, mirroring `create_documents`) fed token-unit chunks: count of −1 and wrong offsets | Corpus D, our chunker's spans re-cut by a tiktoken window splitter written in the notebook | shows the mechanism of issue #29884 without installing LangChain (the library itself is shown in the LLMOps notebook) |
| 12 | Toy dilution cosines | 2-D toy | 1.000 / 0.707 / 0.447 / 0.316 / 0.243 (07 D.7) |

Every expected value goes into a `C2_VERIFY_FACTS.md` table (as P3 has), and each cell asserts it.


### 8. Apply-it tool plan and real-world checklist

**Tool:** `study/tools/chunk_fit_check.py` ("does this chunking suit MY documents and MY embedder?"), modelled on `bm25_fit_check.py`: a command-line tool that can also be imported, and writes a Markdown report. Standard library plus numpy, PyMuPDF, `tokenizers`/`transformers`, tiktoken; no API call by default.

**Inputs**
- `--docs` PDF/TXT/MD files or a folder (PDF via PyMuPDF `page.get_text()`, pages joined with `"\n"`, no cleaning, exactly as v0).
- `--chunker recursive|fixed`, `--size`, `--overlap`, `--unit chars|tokens:<tokenizer>` (e.g. `tokens:minilm`, `tokens:cl100k`), `--scope per_page|cross_page`, `--separators`.
- `--embedder minilm|bge-small|cohere-v4` → its cap and tokenizer (MiniLM 256 and bge 512 from the cached `tokenizer.json`, pinned revision; Cohere v4: cap 128k from [C2-3]; its token counts use a cl100k proxy, labelled as a proxy until a Cohere tokenizer is available).
- Optional `--spans spans.jsonl`: `{"doc": "...", "quote": "..."}` or `{"doc", "page", "char_start", "char_end"}` (the M1 span format); quotes are located once by exact match and reported if not found or found twice.
- Optional `--compare size/overlap` pairs for a side-by-side table.

**Outputs (report sections)**
1. Corpus: documents, pages, characters, chars per token (embedder tokenizer and cl100k).
2. Chunks: count, length distributions in chars and embedder tokens (min / p50 / p95 / max), tiny chunks (< 25% of size), `params_hash`.
3. Truncation: chunks over the cap, rate, and the share of characters that would be lost.
4. Overlap: requested vs real overlap (chars and tokens), zero-overlap pairs.
5. Boundaries: share of sentence ends that coincide with a chunk end; mid-word cuts; page-break cuts (pages ending without terminal punctuation; orphaned-heading candidates).
6. Spans (if given): each span wholly contained in some chunk? Cut by a boundary? Crossing a page in per-page scope? P(contained) predicted vs observed.
7. Duplicates: lines repeated on ≥ 3 pages (boilerplate), identical chunks.
8. Integrity: offset round trip, coverage, forward progress, deterministic ids on two runs.
9. Checklist and recommendation.

**Real-world checklist**

| # | Check | Auto / manual | Pass rule |
|---|---|---|---|
| K1 | The unit of size **and** overlap is written down | auto (config) | `unit` present; overlap < size in the same unit |
| K2 | Characters per token measured for this corpus with the embedder's tokenizer | auto | reported; warn if it differs from 4 by > 25% |
| K3 | No chunk over the embedder cap | auto | truncated = 0 (or a written reason) |
| K4 | Chunks are not far below what the model handles well | manual | MiniLM: compare with its 128-token training length (model card); decide by I1, not here |
| K5 | Real overlap matches the intent | auto | median real overlap ≥ 50% of requested; count zero-overlap pairs |
| K6 | Few tiny tail chunks | auto | < 5% of chunks under 25% of size |
| K7 | Gold spans are not cut | auto (with `--spans`) | ≥ 90% of spans wholly inside a chunk; list the rest |
| K8 | Page-break damage known | auto + manual | count pages that end mid-sentence; read 5 by eye |
| K9 | Offsets round-trip; ids deterministic | auto | 100% |
| K10 | No repeated boilerplate inside chunks | auto + manual | repeated lines listed; decide in C1 whether to strip (new snapshot) |
| K11 | Tables, lists and headings survive | manual | open 10 random chunks; tick headings kept with their body |
| K12 | `params_hash` and tokenizer id recorded with the index | auto | present in the report header |

**Recommendation logic**
- K3 fails → lower the size (in the embedder's tokens) **or** change the model for the whole corpus; never mix.
- K1 or K5 fails → fix the configuration first; results are not comparable yet.
- K7 below 90% with the spans short (F ≤ O + 1 for most) → raise overlap; with long spans → structure-aware chunking (I2) or a query-time window (X1).
- K8 high in per-page scope → try a cross-page arm in I1, accepting two-page citations.
- K6 high → merge tail chunks under a minimum length (an I1/I2 variant), or accept and record.
- Everything passes → keep the configuration; tune size only in I1 with retrieval metrics.


### 9. LLMOps notebook plan

`study/llmops/notebooks/C2_chunking_llmops.ipynb` (folder confirmed when the helper package is built). It applies Foundation §12 row "2 · C1–C2": **no external calls; loader and splitter comparison; chunk stats in the trace; chunk-property tests; build time; `params_hash`; T1.** It runs after the lesson and the lab.

**External calls (cached):** none. Tokenizers run locally (MiniLM `tokenizer.json`, tiktoken). The optional Cohere tokenizer would need one Models API call for `tokenizer_url`; that is **decision 2** in the notes, and it would go through `llmops.cache` like any call. Replay mode is trivially satisfied; the notebook is still executed in the `replay` CI tier, so it must never open a socket (`HF_HUB_OFFLINE=1`).

**Framework build: pieces mapped to the mechanism**

| Framework piece | Lesson step | Hidden default the lesson warns about |
|---|---|---|
| `RecursiveCharacterTextSplitter()` with **no arguments** | recursive split + merge | `chunk_size=4000`, `chunk_overlap=200`, `length_function=len` (Foundation §9.2): v0 would silently get 4,000-char chunks |
| `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len, add_start_index=True)` per page | v0 settings | `strip_whitespace=True` changes chunk text (so `text != doc[a:b]` when edges are spaces); `keep_separator=True` puts the separator at the *start* |
| `RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=200, chunk_overlap=50, add_start_index=True)` | the unit trap | encoding `gpt2` by default; overlap in tokens; `start_index` −1 or wrong ([C2-1], issue #29884) |
| `TokenTextSplitter(chunk_size=200, chunk_overlap=50)` | exact token windows | decodes windows separately; no offsets |
| `split_documents(pages)` vs `split_text(doc_text)` | per-page vs cross-page scope | per-page restarts at 0 and never crosses |
| Course chunker (`ragkit` / lab reference) | the mechanism | — (the reference) |
| A `CourseChunker(TextSplitter)` adapter (about 15 lines) that returns `Document`s with our `char_start`, `char_end`, `page_segments`, `chunk_id`, `params_hash` in metadata | how to plug our chunker into LangChain later (C3/C4 retrievers) | none; it shows the framework can carry exact offsets if we give them |

**Comparison experiment (the "previous version" here is the course chunker = v0).** On Corpus D, per page, 1000/200 chars: LangChain vs ours, per chunk: same count? same boundaries (Jaccard of boundary sets)? text equality after stripping? `start_index` equal to our `char_start`? Then the same for the token-unit splitters (expected: offsets break). No retrieval metric: that starts at C3/C4 and v0.1.

**Tracing.** The default is the plain JSONL trace (Foundation §3.2). Foundation §3.3 has no span for index building, so this concept proposes one **"chunk/index-build" span**: `run_id`, `snapshot_id`, `chunker`, library name and version, `params_hash`, unit, tokenizer id, n_docs, n_chunks, chars and embedder-token length stats (min/p50/p95/max), truncated count, tiny-chunk count, real-overlap stats, round-trip pass, build time. Phoenix (local) can display it via `arize-phoenix-otel`; LangSmith only for Corpus D under `privacy.assert_corpus_is("D")` (Foundation §3.2). Chunk text is never exported; ids and stats only.

**Dataset and evaluators** (`code-based-evaluators`; no judge, D-10):
- Golden artefact: the v0 `chunks.jsonl` (97 lines, sha256 `d4108b89…011b`, C2LAB_FACTS) as a regression fixture.
- T1 property tests (pytest; optionally `hypothesis` for random texts): round trip; size bound in the declared unit; coverage (no gaps); forward progress; per page never crosses; deterministic ids across two runs; `params_hash` changes when any field changes (unit, scope, separators included); real overlap ≤ requested; truncated == 0 for the configured embedder; the 97-record fixture unchanged.
- Gold-span check (once M1 exists): share of gold spans wholly inside a chunk, per configuration; feeds I1.

**Cost, latency and tokens.** No money. Report build time p50/p95 over 5 runs (per page and cross page), chunks per second, and **embedding tokens per corpus** (sum of embedder tokens), which is the input to C3's cost estimate (Cohere price still **UNVERIFIED**, Foundation §6.2).

**Config versioning.** The chunking block lives in the run's `config.yaml` (06 §2.4); `params_hash` is computed from it with the 06 recipe; the library versions (`langchain-text-splitters`, tokenizer files and revision) go into `env.json`. A chunking change is a new `params_hash`, a new index folder and a new experiment (06 §9.1).

**Monitoring and feedback** (`ci-cd-evals`, `error-analysis`). The apply-it tool's report is the "production" signal for new documents. Alerts in `monitor.yaml`: truncation rate > 0 for the configured embedder; tiny chunks > 5%; chars/token outside the corpus's recorded band by > 20% (a parser change or a new language); boundary cuts through gold spans > 10%; round-trip failures > 0. A confirmed failure goes to the M5 error log, then becomes a T1 fixture.

**Place in the lifecycle.** Analyze: chunk stats and boundary cuts (`trace-data-analysis` later, at scale). Measure: property tests and the span-cut rate (`code-based-evaluators`; `rag-evaluation` starts at C4). Improve: belongs to I1–I2. dev → CI: T1 and the `replay` marker. Monitoring: the apply-it reports. Skills used: `evals-foundations`, `code-based-evaluators`, `llm-observability`, `ci-cd-evals`, `rag-evaluation` (for the retrieval/answer split it hands to C4/M2).


### 10. Tools, frameworks, libraries and LLMs

Pins: newest release on or before 2026-10-03 (PyPI JSON, read 2026-10-17). "Installed" from `uv pip list` (read-only).

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| PDF text (v0 snapshot) | `pymupdf` | 1.26.7 (pinned) | yes | yes | — | AGPL-3.0 (or commercial) | yes (pinned for `snapshot_id`) |
| Course chunker | plain Python (lab reference / `ragkit/chunking.py`) | — | (lab) | yes | — | ours | yes: mechanism first |
| BPE token counts | `tiktoken` (`cl100k_base`, `gpt2`) | 0.14.0 | yes | yes once the encoding file is cached | — | MIT | yes (counting only; no OpenAI calls) |
| Embedder tokenizers | `tokenizers` + cached `tokenizer.json` (MiniLM rev `1110a243…`; bge-small) | 0.23.2 (keep; newest stable ≤ 10-03; 1.0.0rc2 is a pre-release) | yes | yes (`HF_HUB_OFFLINE=1`) | — | Apache-2.0 | yes |
| Runtime truncation check, fallback embedder | `sentence-transformers` + `all-MiniLM-L6-v2` | 6.1.0 (keep) | yes | yes | — | Apache-2.0 | yes (D-03 fallback) |
| Default embedder (facts only in C2) | Cohere `embed-v4.0` | API | n/a | no | **0 calls in C2**; optional 1 Models-API call for `tokenizer_url` (decision 2) | service terms | yes (D-03) |
| Charts | `plotly` | (installed) | yes | yes | — | MIT | yes |
| Property tests | `pytest` | 9.1.1 | yes (dev) | yes | — | MIT | yes |
| Random property tests (optional) | `hypothesis` | 6.168.3 | no | yes | — | **MPL-2.0** | yes (dev group only); optional, the lab's seeded random sweep already covers it |
| Framework splitters (LLMOps notebook only) | `langchain-text-splitters` | 1.1.3 (needs `langchain-core>=1.4.7`) | no | yes | — | MIT | yes (D-32, after the mechanism) |
| Framework core | `langchain-core` | 1.6.6 (requires `langsmith>=0.3.45`) | no | yes | — | MIT | yes |
| Reading only | `llama-index-core` (`SentenceSplitter`) | 0.14.25 | no | — | — | MIT | **not installed**; read the source only |
| Reading only | `chunking_evaluation` (Chroma) | git only, no PyPI | no | no by default (OpenAI embeddings in examples) | — | MIT | reading only (no OpenAI) |
| Not needed | `chonkie` 1.7.0, `semchunk` 4.1.1 | — | no | — | — | MIT | skip: they hide the mechanism C2 teaches |
| LLM per task | Groq `openai/gpt-oss-20b` | — | — | — | **0 calls**: C2 has no LLM step | — | yes |
| LLM per task | Claude (Haiku/Sonnet 5.5) | — | — | — | **0 calls**: not worth it for C2 | — | n/a |
| LangGraph | `langgraph` | 1.2.12 | no | yes | — | MIT | **not needed** for C2 (linear, no control flow) |
| Hosted tracing | `langsmith` | 0.14.4 (Foundation pin) | no | SDK yes | free plan; Corpus D only | MIT | yes, optional; chunk stats only |
| Local tracing | plain JSONL trace (default); `arize-phoenix-otel` 0.17.2 to view | — | no | yes | — | Apache-2.0 | yes |

**Install lines** (do not run until the LLMOps notebook is built; the Foundation's `llmops` group):

```text
uv add --group llmops langchain-core==1.6.6 langchain-text-splitters==1.1.3 langsmith==0.14.4
uv add --group dev hypothesis==6.168.3          # optional
```

**Keys needed:** none for the lesson, verify notebook, tool and LLMOps notebook. `LANGSMITH_API_KEY` only if Yash mirrors Corpus D chunk stats to LangSmith (optional). `COHERE_API_KEY` (already present) only if decision 2 is "yes".


### 11. Open questions for Yash (preferences only)

1. In the apply-it tool, do you want to give gold spans as **quoted text** (easier to write, matched once) or as **page + offsets** (exact, the M1 format)? Both can be supported; which should the examples use?
2. Should the HTML lesson keep the interactive slider (window size, overlap and fact length) in **Short** mode, or only in Full?
3. For your own documents, do you want the tool's default embedder to be **MiniLM** (shows truncation, fully offline) or **Cohere v4** (your real default, where truncation is almost never the issue)?

---

## Concept C3: Embedding and indexing with metadata

### 1. Sources checked

**External sources** (numbered; details and results in §5; URLs in Notes (f)): [C3-1] Cohere Embed API v2 reference (verified) · [C3-2] Cohere Embed models / Models / Embeddings guide (verified; price and normalisation UNVERIFIED) · [C3-3] Cohere rate limits (verified) · [C3-4] Sentence Transformers docs = Ext C#17 (verified) · [C3-5] FAISS wiki (verified) · [C3-6] Chroma docs (verified) · [C3-7] sqlite-vec docs (verified; exhaustive-vs-ANN UNVERIFIED) · [C3-8] Matryoshka Representation Learning, Kusupati et al. 2022 (abstract verified). Also: LangChain `InMemoryVectorStore` source (master, verified), PyPI JSON (verified), installed SDK sources (read locally). LanceDB docs were not opened (UNVERIFIED).

**Book pages (opened 2026-10-17, PyMuPDF text of each page):**

| Cite | What is there (paraphrase) | 02/04 claim |
|---|---|---|
| Ch1 p.5/14 | Step 3 cleaning (tabs, whitespace, line ends; dirty text gives noisy vectors); Step 4 embeddings as "coordinates of meaning" | 02 ok |
| Ch1 p.6/14 | Similar topics land near each other; Step 5 stores vectors in a "vector database", FAISS named, fast nearest-neighbour search | 02 ok; FAISS-as-database is DV-04 |
| Ch1 p.7/14 | Library analogy; five-step preparation sketch: load, split ~1000/~200 chars, **clean each chunk**, embed, store | 02 ok; **04 stops at p.6** |
| Ch8 p.4/11 | Tag each chunk with its sequential position; keep a way to fetch any chunk by that number (memory, side store, or metadata) | 02 and 04 ok |
| Ch14 p.9/13 | "The Role of Metadata": the page-number link is what joins the summary store to the chunk store; stage 2 filters chunks by page | 02 and 04 ok |
| Ch14 p.10/13 | Figure of matching tags; richer schemes use document id + section number for many documents | 02 and 04 ok |
| Also checked (lesson's extra pages) | Ch7 p.4/11 and Ch16 p.4/11 (technique changes only preparation); Ch11 p.6/13 (generated questions stored with a pointer to the source chunk); Ch11 p.10/13 (preparation-time vs query-time cost, regenerate when the collection changes); Ch13 p.6/13 (document vectors precomputed and stored, only the query is embedded live); Ch15 p.12/12 (no index or model change needed); App p.16/23 (glossary: Embedding; FAISS called a vector database), App p.22/23 (Vector; Vector Database/Store) | all as the lesson's G.1 says |

What the book does **not** have (confirmed by the C3 lesson's whole-book scan and by grep here): model ids or versions, `input_type`, normalisation, truncation limits, hashing, manifests, caching, re-indexing. The word "metadata" appears 27 times across the 9 chapters extracted, always as a pointer (position, page, parent), never as a schema.

**Repo cells (`upstream/RAG_Techniques` @ `009adba`, 0-based, read from the .ipynb JSON 2026-10-17):**

| Cite | What it shows | 02/04 claim |
|---|---|---|
| `local_rag_huggingface_faiss.ipynb` cell 10 | Config cell: `EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"` (id, no revision), 1000/200 chars, `TOP_K = 3` | — |
| same, cell 12 | `PyPDFLoader` + `RecursiveCharacterTextSplitter(length_function=len)`; prints `chunks[0].metadata` (source, page only) | — |
| same, cell 14 | `HuggingFaceEmbeddings(..., encode_kwargs={"normalize_embeddings": True})`, comment "Required for cosine similarity" | — |
| same, cell 16 | `encode_to_faiss` = `FAISS.from_documents(chunks, embeddings)`; `save_local` / `load_local(..., allow_dangerous_deserialization=True)` **commented out** | 02 ok (it is `encode_to_faiss`), but nothing is persisted |
| `context_enrichment_window_around_chunk.ipynb` cell 13 | `split_text_to_chunks_with_indices`: raw slicer; `metadata={"index": len(chunks), "text": text}` where `text` is the **whole document** | 02's ⚠ claim **verified** |
| `simple_rag.ipynb` cell 10 | Local `encode_pdf`: split, `replace_t_with_space` **after** splitting, `get_langchain_embedding_provider(OPENAI)`, `FAISS.from_documents`; nothing persisted | 04 ok |
| `hierarchical_indices.ipynb` cell 11 | Adds `chunk_id: i` (position in the list) and `page` to chunk metadata; summaries carry `page` and `summary: True` | — |
| `hierarchical_indices.ipynb` cell 13 | "If both folders exist, `load_local`; else build and `save_local`", with `allow_dangerous_deserialization=True`; folder names carry no settings | 04 ok |
| `helper_functions.py` L48–L76, L338–L358 | `encode_pdf` uses `OpenAIEmbeddings()` at L73 (no model); `get_langchain_embedding_provider` returns `OpenAIEmbeddings()` / `CohereEmbeddings()` with no model and ignores its `model_id` argument | 04's "L352–L354" is only the OpenAI branch (lesson G.2 already reports this) |
| Repo-wide grep | `input_type`: 0 files. `normalize_embeddings`: 1 file (the HF FAISS notebook). "manifest": 0 files | — |

**AE book (paraphrase only):** AE Ch7, 'Common Pitfalls' (do not rely on one end-to-end score; chunking alone moves Recall@k with the same retriever) and 'Metrics for Retrieval Quality' are the method behind the C3 LLMOps retrieval-regression check. AE Ch9 (CI) covers golden-set regression. Nothing in AE is about index files or embedding caches.

**Interview repo** (`upstream/AI-Engineer-Interview-Questions`, MIT, "Copyright (c) 2026 Om"), `04-rag-and-retrieval/questions.md`:
- Q14 "What metadata would you attach to each chunk, and what does it buy you?" (provenance, access control, lifecycle, **pipeline lineage**: model name and version, parser and chunker version, content hash). Closest match to C3.
- Q15 "Many embedding models tell you to prefix queries and documents differently, or to pass a task instruction. Why, and what goes wrong if you ignore it?" (C3's `input_type` in the key and manifest).
- Q18 "What are the tradeoffs of embedding dimensionality, and what are Matryoshka embeddings?" (embed-v4.0 `output_dimension`; renormalise after truncation).
- Q22 "How do you choose a vector database? pgvector vs dedicated vector stores vs search engines." (§5 storage comparison; "keep raw text elsewhere so you can re-embed").
- Q7 (choosing an embedding model), Q29 (keeping an index fresh: **D3**, link only), Q33 (near-duplicates).
- Coding: `12-coding-challenges/08_semantic_search_rag.py` (deterministic embedder, salted `hash()` trap, unit vectors, argpartition top-k).

**Existing course files read (2026-10-17):**
- `concepts/C3_embedding_indexing.md` (714 lines, Parts A–M, written 2026-10-08 before the house style). Measured on MiniLM-L6/L3 only; every Cohere fact except dim 1,536 and context 8,192 is UNVERIFIED there (its own Verification log).
- `sources/verification/C3/C3_FACTS.md` (S1–S9, S-src 90 checks, LT), `c3_measure.py`, `c3_sources.py`.
- `labs/C3_indexing_lab.ipynb` (Tasks 1–8; Task 8 Cohere off by default).
- `progress/O2_smoke_test_2026-10-08.json`: Cohere models API listed `embed-v4.0` context_length 8,192, dim 1,536 (default); also lists `embed-v5.0-fast` and `embed-v5.0-pro` (8,192).
- 02 card C3 (lines 347–365), 03 rows 41–42 and edges C2→C3, P5→C3, C3→C4, 04 row C3 (line 136) and DV-04, 06 §2.4 (config, interface table), §2.5 (trace), §3.1–3.2, 08 D-03, D-06, D-32, RK-19, E-3, LLMOps Foundation (§2.3, §2.6, §6.2, §8.4, §9.2, §9.3, §12, E1–E2).
- Tracker: C3, P4, P5, C2, C4 all `not_started`. Open misconceptions touching C3: MC-001 (tokens vs characters; truncation), MC-002 (missing query-embedding step), MC-003 (index time vs query time).

### 2. Gap audit

Sources of ideas: Ch1 p.5–7/14, Ch8 p.4/11, Ch14 p.9–10/13 (plus the lesson's extra pages); the C3 lesson (Parts A–M), its lab (Tasks 1–8) and Part L items; repo cells above; Cohere and sentence-transformers docs; interview Q14, Q15, Q18, Q22. Tracker: every owner concept below is `not_started` (P1, P4, P5, C1, C2, C4, R2, D3), so "Yash studied it?" is **no** throughout; a bridge must be taught inside C3, not assumed.

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | An embedding is a fixed-length vector of meaning; one model = one vector space | Ch1 p.5–6/14; every C3 step | Lesson points to P4 only | P4 | no | bridge | Two sentences + a 2-D picture (Short) |
| 2 | Cosine vs dot vs L2; unit vectors make all three rank the same (‖a−b‖² = 2 − 2 a·b) | D.5 normalise; FAISS `IndexFlatL2` default; Chroma `l2` default | Lesson cites P4 D.3, not taught here | P4 | no | bridge | One formula line + "normalise once, assert at load" (Short) |
| 3 | Query/document asymmetry: `search_document` for chunks, `search_query` for questions; `classification`, `clustering` exist too | A4, D.4, D.6, lab Task 8 | Lesson names the two values only | P4 (D.8) | no | bridge | Short table of the 4 text values; why the query side is not an index change |
| 4 | Max input length and **silent truncation**, counted in the model's **tokens**, not characters | 06 §3.2, RK-19, D-06; tool check | Missing in C3 (07 D.6 has the MiniLM numbers); MC-001 open | C3 (with P1, C2) | no | **core** | New section: MiniLM 256 tokens; Cohere `truncate=END` default; limits 8,192 (API) vs 128k (docs) conflict; bound: a 1,000-char chunk cannot reach 8,192 tokens if tokens ≤ UTF-8 bytes (≤ 4,000) — assumption, see §6 |
| 5 | `output_dimension` (256/512/1024/1536) and Matryoshka: smaller prefix vectors; renormalise after cutting | Foundation E2; interview Q18 | Missing | C3 (key field); depth in P5 | no | core (Short: 2 lines); Full: Matryoshka | Put it in the key and manifest; Full: one paragraph + [C3-8] |
| 6 | `embedding_types` (float, int8, uint8, binary, ubinary) | Foundation E2 | Missing | C3 (key); quantisation is P5/D2 | no | core (key only) / next (quantisation) | Key field; quantisation link only |
| 7 | Batch limit 96 texts per call; `ClientV2.embed` does not batch; calls = ⌈N/96⌉ | LLMOps cost; 06 §2.4 `batch_size: 64` | Missing (06 says "check at O2") | C3 | no | core | One line + the Corpus D count: 97 chunks → 2 calls |
| 8 | Batch size changes float bits (1.34e-07), so "rebuild from scratch" ≠ byte-identical; the cache gives byte-identical rebuilds | D.7 | Taught (D.7) | C3 | no | core | Keep; add "API models: also server drift → canary" |
| 9 | Chunk record: `doc_id`, `snapshot_id`, `chunk_id`, `seq`, offsets, `page_segments`, `text_sha256` | D.2, H.4 | Taught (D.2) but relies on C1/C2 | C2 (07 D.9) | no | bridge | Keep the one real record; one line per field: "what breaks without it" |
| 10 | `snapshot_id`: frozen extracted text; parser version changes it | D.1, rebuild rule | Taught briefly (E row) | C1 / 06 §5.3 | no | bridge | Keep, one line |
| 11 | `params_hash`: canonical JSON (`sort_keys`), sha256, not `hash()`; a hash that ignores a field is worse than none | D.3, lab Task 1 | Taught (D.3) | C3 | no | core | Keep; Short version needs the 92/89 example |
| 12 | Content-addressed cache key; separator ambiguity (`"|"` guard) | D.4, lab Task 2 | Taught, but **fields incomplete** (no `output_dimension`, `embedding_type`, `truncate`, `max_tokens`) | C3 | no | core | Switch to the Foundation canonical-JSON key for new code; keep the old string form for existing vectors (§4 E-C3-3) |
| 13 | `embed_hash` and the folder `index/<snapshot>/<params>/<embed>/` | H.4, lab Task 4 | Taught (H.4) | C3 | no | core | Teach the six fields + the three missing ones; flag the query-`input_type` quirk |
| 14 | Model identity: id vs revision vs weights; API models have `revision: null` and can change silently | H.4 manifest; canary | **Missing**: lesson treats revision as complete identity | C3 (identity); D1/D3 (monitoring) | no | core | Short: "an API id is a name, not a version: record the date and run a canary"; HF: weights sha256 (two cached MiniLM snapshots share weights) |
| 15 | Manifest + fail-closed loader (file sha256, dtype, shape, unit rows, settings vs run config); `allow_pickle=False` | D.5, lab Task 6 | Taught (D.5) | C3 | no | core | Keep |
| 16 | Rebuild rule: snapshot, chunker, document-side embedding → rebuild; k, prompt, LLM, reranker, query `input_type` → reuse | D.6, lab Task 5 | Taught (D.6); MC-003 open | C3 | no | core | Keep; add the new embedding fields to the rebuild side |
| 17 | Rebuild ≠ re-embed (cache hits after edits) | D.6, S4, S8 | Taught | C3 | no | core | Keep numbers 96/97, 12/65 |
| 18 | Row alignment: row *i* of `vectors.npy` ↔ line *i* of `chunks.jsonl`; never assume `seq == i` | H.4, C4 | Taught in H.4; owner P5 D.4 | P5 | no | bridge | Keep |
| 19 | Mixed models in one index: how to detect (one manifest per folder; recompute keys; re-embed a sample) | Interview Q14; tool | **Missing** | C3 | no | core | New Short section + tool check |
| 20 | Duplicate and near-duplicate chunks (`text_sha256` collisions; cosine ≥ 0.98 pairs) | S1 "no duplicate texts"; C4 near-duplicate distractors | Missing (measured, never taught) | C3 (detect); C4 (effect on ranking) | no | core (detect) / bridge (effect) | Tool check + one line |
| 21 | Where to store: `.npy`+JSONL vs FAISS vs Chroma vs LanceDB vs sqlite-vec; "FAISS is not a database" (DV-04) | Ch1 p.6/14; K "later a vector database" | Partly (K, B.1) | C3 (choice at v0); P5 (exact vs ANN) | no | core (Short: table) | Comparison table in Full; one-line verdict in Short (§5) |
| 22 | Exact vs approximate search (why no ANN at ~100–5,000 chunks) | storage choice | Missing here; owner P5 | P5 | no | bridge | One line: N × d multiply-adds per query; ANN only past ~10⁵–10⁶ vectors |
| 23 | Metadata as a filter key; pre- vs post-filtering | Ch14 p.9/13; 04 DV row 12 | Not here | R2 | no | next | Link; C3 stores the fields R2 will filter on |
| 24 | Incremental re-indexing, deletes, orphans | lesson L.3 transfer item; interview Q29 | Not here | D3 | no | next | Link only (the transfer item already previews it) |
| 25 | Embedding cost and calls; trial cap 1,000 calls/month; 2,000 inputs/min | LLMOps | Missing | C3 / D2 | no | core (LLMOps) | Count calls per build |
| 26 | Privacy: chunk text leaves the machine with Cohere; book text never (D-32) | Task 8; LLMOps | Missing in lesson | D4 / Foundation §2.4 | no | bridge | One line + the privacy guard |
| 27 | Full document copied into every chunk's metadata (repo anti-pattern) | 02 card ⚠; G.2 | Taught (G.2, 26.3 M characters) | C3 | no | core | Keep as a "spot the bug" item |
| 28 | Pickle risk (`allow_dangerous_deserialization`) | B.1, H.2 | Taught | C3 | no | core | Keep |

**Ideas already taught well and kept:** the three identities (snapshot, params, cache key), `params_hash` properties (S2), the stale-index replay (97 vs 201), the text-only-key bug (97/97 stale hits, rank 3 → 16), unit-row assert (L3 7/34), and the rebuild table (16 scenarios).

### 3. Quiz coverage

**No question file exists** (`study/questions/` holds only P3 and R1). The lesson's Part L has 3 Recall, 3 Application and 1 Transfer item, but they were written for the long Parts A–M lesson, and none tests the new ideas found in §2 (#4–#7, #14, #19, #20). A Short reading must answer every key point below.

Needed question titles (FORMAT.md ids):

| Id | Type | Title (one question each) | Key points come from §6 idea |
|---|---|---|---|
| C3-PRE-01 | pre-test | "Besides the text, what must each stored chunk carry, and what breaks without it?" (O1-Q05 retest, scored 1 at confidence 3) | 3 |
| C3-PRE-02 | pre-test | "You change the overlap from 200 to 100. Can you keep the stored vectors?" | 7, 8 |
| C3-R-01 | recall | "Name the three index files and what each holds." | 6 |
| C3-R-02 | recall | "Which fields go into the embedding cache key, and why not the chunk id?" (now incl. `output_dimension`, `embedding_type`, `truncate`) | 5 |
| C3-R-03 | recall | "Two changes that force a rebuild, two that do not." | 7, 8 |
| C3-R-04 | recall | "What does Cohere do by default with a text longer than its limit, and how would you notice?" | 9 |
| C3-R-05 | recall (interview) | Interview repo Q14 "What metadata would you attach to each chunk, and what does it buy you?" (quoted with the MIT notice; our answer first, the repo answer after the attempt) | 3, 10 |
| C3-A-01 | application | "Overlap doubles: what happens to `params_hash`, chunk ids and the cache?" | 4, 7, 8 |
| C3-A-02 | application (debugging) | "This cache passes on MiniLM. What is wrong?" (text-only key) | 5 |
| C3-A-03 | application | "How many bytes is `vectors.npy` for 97 chunks at 1,536 dims, and how many Cohere calls does the build need?" (596,096 B; 2 calls) | 6, 9 |
| C3-A-04 | application | "Your loader finds rows with norm 2.4. Which step is missing, and does it change the top-k?" | 2, 6 |
| C3-A-05 | application | "An index folder holds vectors from two models. Which checks catch it, with and without the cache?" | 10 |
| C3-T-01 | transfer | 40,000 manuals, 200 change nightly, model change next quarter (lesson L.3) | 7, 8, 10 |
| C3-T-02 | transfer (interview) | Interview repo Q22 "How do you choose a vector database? pgvector vs dedicated vector stores vs search engines." applied to 5,000 chunks on a laptop | 11 |

Key points the current lesson cannot answer from any Short text: R-04 (truncation default, limits), A-03 second half (batch of 96), A-05 (mixed-model detection), T-02 (store comparison), and the new key fields in R-02.

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| E-C3-1 | 06 §2.4 `embedding` block and `cache.embeddings` comment; C3 lesson D.4, H.4; lab Task 2 (`embedding_cache_key`), Task 4 (`embed_hash`), Task 8 (cell 37) | Foundation **E2 confirmed in code**: `output_dimension`, `embedding_types` and `truncate` are in neither the key nor `embed_hash`; Task 8 sends none of them, so the server defaults (1536, float, END) are used and not recorded. `max_tokens` (a newer request field) is also missing | [C3-1]; lab cell 37 read 2026-10-17 | Send all four explicitly; add them to the key (Foundation §2.3 canonical JSON) and to `embed_hash`; for MiniLM record `"none"` |
| E-C3-2 | O2 report, 08 E-3, C3 lesson (Source references, F Step 3) say `embed-v4.0` context **8,192**; Foundation §6.2 says **128k** | Two sources disagree. The models API (2026-10-08) returned 8,192; the docs page (2026-10-17) says 128k | O2 JSON; [C3-2] | Record both with dates; mark the effective limit **UNVERIFIED**; one recorded probe at C3 (§7) settles it |
| E-C3-3 | 06 §3.2 Cohere row | Still "UNVERIFIED: read at O2" although O2 recorded dim 1,536 and context 8,192 | O2 JSON | Fill from O2 and [C3-2], with the conflict |
| E-C3-4 | 06 §2.4 `batch_size: 64  # [P]; check the provider's batch limit at O2` | The limit is 96 texts per call; `ClientV2.embed` sends one request and does not split (the v1 `Client.embed` splits at 96 and sends batches **concurrently**) | [C3-1]; cohere 7.2.0 `config.py`, `client.py` L182–226, `v2/client.py` L444 | Batch at 96 in `CachedEmbeddings` (Foundation §9.3 already says so); drop the 64 or label it MiniLM-only |
| E-C3-5 | C3 lesson H.4 / lab Task 4: `embed_hash` includes the **queries'** `input_type` | A query-side change creates a new index folder, although D.6 says query-side changes need no rebuild. The lesson admits it ("building that folder re-embeds nothing") | Lesson H.4 | Decide: hash only the document side for the folder, keep the query side in the manifest (an interface change, so the coordinator/Yash decides; §11) |
| E-C3-6 | C3 lesson H.4, manifest `revision` | A revision is treated as the model's whole identity. Two cached MiniLM snapshots (`1110a243…`, `c9745ed1…`) have identical weights and tokenizer, so a README-only bump would force a rebuild. For API models `revision: null` hides silent server changes | HF cache sha256 (§1) | Add `weights_sha256` (HF) as a check field, and the canary (Foundation §8.4) for API models |
| E-C3-7 | C3 lesson Part K "Later: a vector database replaces `vectors.npy` (D4)" | D4 is security; ANN and storage scale belong to P5 (and D2 for cost). Same slip the external review §3 #31(b) reported; still open | Lesson K; review #31 | Point to P5/D2 |
| E-C3-8 | 04 C3 row (line 136) | Book pages stop at Ch1 p.6/14; p.7/14 (the preparation sketch, "clean each chunk" after splitting) is where the offset problem starts. Already listed in lesson G.2 item 2; still open in 04 | Ch1 p.7/14 opened | Add p.7/14 |
| E-C3-9 | 02 C3 card repo line | Cites `local_rag_huggingface_faiss.ipynb` cell 16 for indexing, but its save/load lines are commented out, so it shows nothing about persistence or metadata; the persistence pattern (and the stale-index bug) is `hierarchical_indices.ipynb` cell 13, which only 04 cites | cells 16 and 13 opened | Add `hierarchical_indices` cells 11 and 13 to 02 |
| E-C3-10 | 04 C3 row "Embedding model never pinned (`helper_functions.py:L352-L354`)" | Already corrected in lesson G.2 item 1 (L73; ids are pinned in some notebooks; revisions never); 04 still unedited | helper L48–76, L338–358 opened | Apply the lesson's correction |
| E-C3-11 | Lesson Verification log "Still UNVERIFIED: Cohere raw norms" | Still unverified: Cohere's docs do not say whether float vectors are unit length (checked [C3-1], [C3-2], Embeddings guide) | — | Keep UNVERIFIED; the verify notebook measures it from one recorded call |

The ⚠ in 02 ("stores the full document in every chunk's metadata", `context_enrichment_window_around_chunk.ipynb` cell 13) is **correct**.

### 5. What the research says

**[C3-1] Cohere Embed API v2 reference** (Cohere, current; https://docs.cohere.com/reference/embed; opened 2026-10-17; verified).
- Facts read on the page: `texts` max **96 per call**; `input_type` required for v3+ with values `search_document`, `search_query`, `classification`, `clustering`, `image`; `embedding_types` default `["float"]`, also `int8`, `uint8`, `binary`, `ubinary`, `base64` (v3+); `output_dimension` only for embed-v4 and newer (values not on this page); `max_tokens` per input (no default stated), longer input cut by `truncate`; `truncate` default **`END`** (`NONE` errors, `START`/`END` cut); `priority` default 0. Response: `embeddings.<type>` arrays, `texts`, `meta.billed_units.input_tokens`, `meta.tokens`, `meta.cached_tokens`, `meta.warnings`.
- **Not on the page:** whether returned float vectors are unit length.
- What it means: three more request fields shape the vector (`output_dimension`, `embedding_types`, `truncate`) and a fourth (`max_tokens`) can shorten the input. All four must be sent explicitly and keyed (Foundation E2), and `meta.warnings` plus `billed_units.input_tokens` should be stored, because they are the only server-side sign of truncation.

**[C3-2] Cohere Embed models page** (Cohere, current; https://docs.cohere.com/docs/cohere-embed and https://docs.cohere.com/docs/models; opened 2026-10-17; verified).
- `embed-v4.0`: context **128k**, dimensions 256/512/1024/1536 (default **1536**), similarity cosine, dot or Euclidean, text + images + mixed. `embed-v5.0-pro` and `embed-v5.0-fast` are now listed (128k; 256–2048, default 2048). v3 models: 512 context. No deprecation is stated for embed-v4.0. Matryoshka is described on the Embeddings guide (https://docs.cohere.com/docs/embeddings, verified) as "coarse-to-fine" vectors chosen with `output_dimension`; that guide has no text batch limit and no normalisation statement, and its own example computes full cosine (divides by both norms).
- **Conflict:** the O2 smoke test (2026-10-08) read `context_length` **8,192** for embed-v4.0 from Cohere's models **API**; the docs page says **128k**. The C3 lesson and 08 E-3 carry 8,192; the Foundation §6.2 carries 128k. Which limit `truncate=END` applies is **UNVERIFIED**. At 1,000-character chunks (~250 tokens) neither limit is reached, so v0 is safe either way; it matters for I1 large-chunk arms and for whole-document embedding.
- Price for embed-v4.0: **UNVERIFIED** (cohere.com/pricing, opened 2026-10-17, shows no per-token embed price; only Model Vault hourly rates for Embed 5).

**[C3-3] Cohere rate limits** (https://docs.cohere.com/docs/rate-limits; verified 2026-10-17): Embed 2,000 inputs/min for trial and production keys; trial keys capped at 1,000 API calls/month (all endpoints).

**Cohere Python SDK 7.2.0, installed** (read as text from `rag_learning/.venv`, not run; library source):
- `config.py`: `embed_batch_size = 96`.
- The v1 `Client.embed` **auto-batches** at 96 and sends the batches **concurrently** through a thread pool (`client.py` L182–L226), default `batching=True`. It has **no `output_dimension` parameter**.
- `ClientV2(V2Client, Client)`: `embed` resolves to `V2Client.embed` (`v2/client.py` L444), which sends **one request** with `model, input_type, texts, images, inputs, max_tokens, output_dimension, embedding_types, truncate, priority`; no batching. The course uses `ClientV2` (O2 smoke test L86, C3 lab cell 37), so the course must batch itself.
- `max_retries` defaults to 2 (`base_client.py` L92–93): hidden retries (Foundation E8).
- C3 lab cell 37 (Task 8) calls `_co.embed(texts, model, input_type, embedding_types=["float"])` with no `output_dimension` or `truncate`, and its cache spec has neither: Foundation E2 is real in the lab code, not only in 06.

**[C3-4] Sentence Transformers docs** (UKP / Hugging Face, current; https://sbert.net/examples/sentence_transformer/applications/computing-embeddings/README.html; opened 2026-10-17; verified; this is 02's **Ext C#17**, which `01_SOURCE_INVENTORY.md` §6 row 17 lists as https://sbert.net/).
- Longer texts are truncated to the first `model.max_seq_length` tokens, silently; the limit can be lowered but not raised past the model's maximum. Prompts are prepended at inference; none is applied by default.
- Installed source (`sentence-transformers` 6.1.0, Apache-2.0, read not run): `encode(..., batch_size=32, precision="float32", normalize_embeddings=False, truncate_dim=None)`; `encode_query` / `encode_document` exist (they apply the model's `query`/`document` prompts if the model defines them; MiniLM-L6 defines none).
- Local HF cache, MiniLM-L6: `modules.json` = Transformer → Pooling → **Normalize**, so `encode()` returns unit vectors even with `normalize_embeddings=False`; `sentence_bert_config.json` `max_seq_length` 256. **Two snapshots are cached**: `1110a243…` (`refs/main`, the pinned one) and `c9745ed1…` (2026-03-31). Their `model.safetensors` and `tokenizer.json` sha256 are **identical** (`53aa5117…`, `be50c362…`); only `README.md` differs. So a revision change does not always mean new vectors, and today `embed_hash` would force a rebuild for a README-only bump. Recording the weights' sha256 in the manifest (as a check, not a key) tells the two cases apart.

**[C3-5] FAISS wiki** (Meta, current; https://github.com/facebookresearch/faiss/wiki/Getting-started and https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances; opened 2026-10-17; verified).
- `IndexFlatL2` is brute force (exact); `search` returns ids and **squared** L2 distances; without explicit ids, an added vector's id is its position; only float32; FAISS stores vectors and integer ids, no text or metadata.
- Inner product is cosine only if vectors are normalised first (`faiss.normalize_L2`), queries too; for unit vectors squared L2 = 2 − 2·cos.
- For the project: at our size `IndexFlatIP` gives the same ranking as `V @ q` and adds nothing but a dependency; metadata still lives in `chunks.jsonl`. LangChain's FAISS wrapper adds a pickled docstore (lesson B.1).

**[C3-6] Chroma docs** (Chroma, current; https://docs.trychroma.com/docs/collections/configure and /docs/embeddings/embedding-functions; opened 2026-10-17; verified).
- Default space **`l2`** (squared), HNSW approximate search (`ef_construction` 100, `ef_search` 100, `max_neighbors` 16); the default embedding function is all-MiniLM-L6-v2, downloaded automatically on first use.
- Hidden defaults that clash with the lessons: the L2 default (not cosine), an approximate index (non-exact top-k), and a silent default embedder. 28 core dependencies (incl. onnxruntime, OpenTelemetry exporters, uvicorn) per PyPI 1.5.9.

**[C3-7] sqlite-vec docs** (A. Garcia, 2024–; https://alexgarcia.xyz/sqlite-vec/ and /features/vec0.html; opened 2026-10-17; verified). MIT/Apache-2.0; docs show v0.1.10-alpha.4, PyPI stable 0.1.9 (2026-03-31), a 0.29 MB wheel, no Python dependencies. `vec0` tables support up to 16 **metadata columns** usable in the KNN `WHERE` (=, !=, <, >…), up to 4 **partition keys** (pre-filter shards) and 16 **auxiliary** columns (stored, not filterable). Whether KNN is exhaustive is not stated on those pages (**UNVERIFIED**). The uv Python here (3.12.8, SQLite 3.45.3) exposes `enable_load_extension` (checked locally). Pre-1.0, so the API may change.

**LangChain `InMemoryVectorStore`** (langchain-core source, master branch, https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/vectorstores/in_memory.py; opened 2026-10-17; verified on master, not on the 1.6.6 pin). Store = dict `id → {id, vector, text, metadata}`; missing ids become **`uuid4`** (non-deterministic); cosine similarity; ties ordered by `argsort()[::-1]` (not by id); `filter` is a callable applied **before** scoring (pre-filter); `similarity_search` default `k=4`; MMR `fetch_k=20, lambda_mult=0.5`; `add_documents` makes **one** `embed_documents` call for all texts (no batching); `dump` writes JSON of the store only and `load(path, embedding)` uses whatever embedder you pass: **no model identity is saved or checked**.

**PyPI (JSON API, 2026-10-17; newest release on or before 2026-10-03):** faiss-cpu 1.15.1 (MIT, 16.3 MB Windows wheel, deps numpy + packaging); chromadb 1.5.9 (Apache-2.0, 23.5 MB wheel, 28 core deps); lancedb 0.39.0 (Apache-2.0, **103 MB** wheel, needs pyarrow; 0.40.0 is newer than the cut-off); sqlite-vec 0.1.9 (MIT/Apache-2.0, 0.29 MB); hnswlib 0.8.0 (2023, **no Windows wheel**: needs a C++ compiler); usearch 2.26.3 (Apache-2.0); langchain-core 1.6.6 (matches the Foundation). None of these are installed now (`uv pip list`).


**[C3-8] Matryoshka Representation Learning** (Kusupati et al., arXiv 2205.13147, 2022, revised 2024; https://arxiv.org/abs/2205.13147; abstract opened 2026-10-17; verified; venue not shown on the page).
- The study: train one encoder so that nested prefixes of its vector (e.g. the first 64, 128, … dimensions) are each usable embeddings; tested on ImageNet-1K/4K classification and retrieval, few-shot long-tail tasks, and vision, vision+language and BERT language models.
- The result (abstract): up to 14× smaller embeddings at the same ImageNet-1K accuracy and up to 14× faster large-scale retrieval.
- Its limits: "up to" figures on image benchmarks; the abstract gives no text-retrieval numbers for our setting.
- For the project: `output_dimension=256` is a different vector, not a slice we can assume equals the first 256 floats of the 1536 one; whether Cohere's server truncates and renormalises is **UNVERIFIED**. So the dimension belongs in the key, and a 256-vs-1536 comparison is an experiment (Full / I-phase), not a free saving.

**Current practice (2024–2026), from the sources above and interview Q14/Q15/Q22:**
- Store lineage beside every vector: model name and version, chunker version, content hash. The interview answer calls this "the one people forget and regret"; our manifest does this per folder, not per row.
- Treat the vector store as rebuildable, never the source of truth: keep raw text and records elsewhere so you can re-embed (Q22). Our `chunks.jsonl` + snapshot already satisfy this.
- Send every output-shaping parameter explicitly; frameworks fill defaults silently (LangChain `CohereEmbeddings` `truncate=None` → server END, Foundation §9.2; Chroma default space `l2` and a default embedder; `InMemoryVectorStore` random ids).
- Hosted embedders version by **name**; a provider can change the model behind a name. Teams detect this with a fixed canary (Foundation §8.4), not with the id.

**Pitfalls, with evidence:**

| Pitfall | Evidence |
|---|---|
| Stale index loaded because the folder name carries no settings | S7: 97 old chunks served instead of 201 (`hierarchical_indices` cell 13 pattern) |
| Cache keyed by text or id serves another model's vectors | S4: 97/97 stale hits, evidence chunk rank 3 → 16 |
| Unnormalised vectors stored | S5: L3 top-4 kept for 7/34 queries |
| Silent truncation | MiniLM: 32/65 chunks over 256 tokens at 2000/400 (07 D.6); Cohere default `truncate=END` [C3-1] |
| Key missing a request field (dimension, type, truncate) | [C3-1]; lab cell 37 (E-C3-1) |
| Whole document copied into each chunk's metadata | `context_enrichment…` cell 13; 26.3 M characters vs 122,774 bytes (S6) |
| Pickled stores | `allow_dangerous_deserialization=True` (hierarchical cell 13; HF-FAISS cell 16 comment) |
| Approximate index presented as exact | Chroma HNSW default [C3-6] |

**How to evaluate C3:** C3 changes no retrieval variable (lesson Part I), so it is judged by **integrity and reproducibility**, not by a quality metric:
- Integrity: the apply-it checks in §8 (all must pass).
- Reproducibility: rebuild twice → identical `params_hash`, ids, `manifest.json` and file hashes (Gate 2→3 item 4).
- Retrieval parity (bridge to C4): the same top-4 for every seed question from (a) our NumPy index and (b) the framework store over the same vectors. Retrieval quality itself (Hit@k, MRR, CE@k) belongs to C4 and M2; answer quality is not touched by C3.

**Interview questions** (from `upstream/AI-Engineer-Interview-Questions`, MIT, "Copyright (c) 2026 Om"; exact titles):
1. Q14 "What metadata would you attach to each chunk, and what does it buy you?"
2. Q15 "Many embedding models tell you to prefix queries and documents differently, or to pass a task instruction. Why, and what goes wrong if you ignore it?"
3. Q18 "What are the tradeoffs of embedding dimensionality, and what are Matryoshka embeddings?"
4. Q22 "How do you choose a vector database? pgvector vs dedicated vector stores vs search engines."
5. Our own, in plain English: "You switch embedding models. How does your system make sure no query is answered from the old vectors?"

**Storage options for ~100–5,000 chunks (recommendation only; the 06 §3.1 decision stands):**

Sizes are derived (float32): 5,000 × 1,536 × 4 = 30.7 MB; 5,000 × 384 × 4 = 7.7 MB. An exact search is N × d multiply-adds per query: 7.7 M at 5,000 × 1,536, a single matrix–vector product (no timing measured here).

| Option | Offline | Licence | Weight (PyPI) | Deterministic top-k | Metadata filtering (for R2) | Hidden defaults | Fit |
|---|---|---|---|---|---|---|---|
| **`.npy` + `chunks.jsonl` + `manifest.json`** (06 §3.1) | yes | ours | none (numpy installed) | yes, exact, ties broken by `chunk_id` | NumPy boolean mask = exact pre-filter | none | **keep (v0 and through R2)** |
| `faiss-cpu` 1.15.1 `IndexFlatIP` | yes | MIT | 16.3 MB, 2 deps | yes (exact) | ids only; metadata elsewhere | `IndexFlatL2` returns squared L2; positional ids | P5 comparison only |
| `sqlite-vec` 0.1.9 | yes | MIT/Apache-2.0 | 0.29 MB, 0 deps | exhaustive or not: UNVERIFIED | metadata columns in the KNN `WHERE`; partition keys | pre-1.0 API | best candidate **if** R2 or D3 wants a single-file store with SQL filters |
| `chromadb` 1.5.9 | yes | Apache-2.0 | 23.5 MB, 28 deps | no (HNSW approximate) | `where` filters | `l2` space; default MiniLM embedder auto-downloaded | avoid (hides what the lessons teach) |
| `lancedb` 0.39.0 | yes | Apache-2.0 | 103 MB + pyarrow | exact by default: UNVERIFIED (docs not opened) | SQL-like filters | not checked | avoid at this size |
| LangChain `InMemoryVectorStore` | yes | MIT | in `langchain-core` | cosine; ties by `argsort` order | callable pre-filter | `uuid4` ids; one embed call for all texts; no model identity on `dump` | LLMOps comparison only |

### 6. Lesson blueprint

**The answer first (draft, 5 sentences).**
1. Embedding and indexing turn each chunk into a vector with one fixed model, and store it next to a record that says where the text came from and how the vector was made.
2. Our index is three files: `vectors.npy` (one unit-length row per chunk), `chunks.jsonl` (the records, in the same row order) and `manifest.json` (every setting that shaped the vectors).
3. Vectors are cached by **content**, a hash of the provider, the model, every request setting and the text, never by chunk id, so a rebuild re-embeds only text that really changed.
4. The index must be rebuilt when the text snapshot, the chunker or a document-side embedding setting changes; k, the prompt, the LLM and a reranker act at query time and never need a new index.
5. The loader compares the manifest with the run and refuses on any mismatch, so a stale or mixed index fails loudly instead of quietly giving worse answers.

**The theory in one read (11 linked ideas; §3's numbers refer to these).**

| # | Idea | Formula / rule |
|---|---|---|
| 1 | An embedding is a fixed-length vector; one model defines one space, so vectors from two models cannot be compared | v = f_model,settings(text) ∈ ℝᵈ |
| 2 | Similarity and normalisation: unit vectors make dot, cosine and L2 rank the same; normalise once at build, assert at load | cos(a,b) = a·b / (‖a‖‖b‖); for ‖a‖=‖b‖=1: ‖a−b‖² = 2 − 2·a·b |
| 3 | The chunk record carries provenance: doc, snapshot, offsets, pages, text hash | `doc_text[char_start:char_end] == text` |
| 4 | `params_hash` names the chunking; the chunk id is for joins only | `params_hash = sha256(json.dumps(chunking, sort_keys=True))[:12]`; `chunk_id = doc:snapshot:params:seq05` |
| 5 | The cache key names one embedding by content and every setting that shapes it | key = sha256(canonical_json{provider, model_id, revision, input_type, output_dimension, embedding_type, truncate, max_tokens, preproc_version, text}) |
| 6 | Three files and a manifest; fail closed | bytes(`vectors.npy`) = 128 + N·d·4; load with `allow_pickle=False`; refuse if any hash, shape, norm or setting differs |
| 7 | The rebuild rule: the index is a function of three things | index = F(snapshot, chunker, document-side embedding settings); anything else is query time |
| 8 | Rebuild ≠ re-embed | calls needed = ⌈(texts whose key is not cached) / 96⌉ |
| 9 | Limits: input tokens (silent cut), batch size, rate | MiniLM 256 tokens; Cohere `truncate=END` by default; tokens ≤ UTF-8 bytes ≤ 4·chars (byte-level tokenizer assumption) |
| 10 | Model identity and mixed indexes: a name is not a version | HF: id + revision (+ weights sha256); API: id + date + canary (max |cos − recorded| ≤ tolerance) |
| 11 | Where to store it: exact NumPy at this size | cost per query = N·d multiply-adds; ANN only when that is too slow (P5) |

**Formula-sheet items:** the 11 rows above, plus: Cohere `input_type` values (search_document / search_query / classification / clustering); `embed-v4.0` dims 256/512/1024/1536 (default 1536); batch ≤ 96 texts; trial cap 1,000 calls/month; `IndexFlatL2` returns squared distances; MiniLM-L6 = 384 dims, 256 tokens, has a Normalize module.

**Step-by-step outline (running example: Corpus D, the climate PDF, 33 pages, 97 v0 chunks; no other data needed).**
1. **Records in:** 97 records from C2, `params_hash 1ca9c5a3b548`, `snapshot ea07572562ac` (S1). Show one record; one line per field: what breaks without it.
2. **Key each text:** build the canonical-JSON key with all settings; show that changing `output_dimension` alone changes it.
3. **Embed the misses:** Cohere: 97 texts → 2 calls (96 + 1); MiniLM: local. Record billed tokens and warnings.
4. **Normalise and check:** norms before/after (MiniLM-L6 already 1; Cohere: measured in §7, UNVERIFIED now).
5. **Write three files + manifest:** 149,120 B at 384 dims (S6); 596,096 B at 1,536 (derived).
6. **Load, fail closed:** refuse a lost line, wrong model, 2000/400 config (S7).
7. **Change things:** page edit → 0/97 ids, 1 miss (S4); 2000/400 → 12/65 hits (S8); model switch → 0 hits (S4); text-only key → 97 stale hits (S4).
8. **Check limits:** token counts per chunk under MiniLM's tokenizer (v0 max 182 < 256; 07 D.6); Cohere bound and probe (§7).
9. **Decide:** rebuild or reuse for 16 changes (S7), now with the three new embedding fields on the rebuild side.

**Visuals that earn their place:**

| Visual | The one thing it shows |
|---|---|
| Pipeline SVG: records → key → cache (hit/miss) → normalise → three files → manifest | Where the cache sits and which identity each file carries |
| Identity grid (rows: 16 changes; columns: snapshot, `params_hash`, `embed_hash`, cache key, rebuild?) | Which hash moves for which change, so "rebuild" is read off, not memorised (MC-003) |
| Cache-hit bars per event (rebuild 97/0, page edit 96/1, 2000/400 12/53, model switch 0/97, text-only key 97 stale) | Content keys make rebuilds cheap and correct; id or text keys make them wrong |
| Token-length histogram per chunk under MiniLM, with the 256 line, for 1000/200 vs 2000/400 | Truncation is invisible unless you count tokens (MC-001) |
| Storage table (not a chart) | At 5,000 chunks everything fits in RAM; exactness and hidden defaults decide, not speed |

**Full-only details:** Matryoshka and int8/binary types; the 8,192 vs 128k conflict and the probe; the `"|"` separator collision; float noise across batch sizes (1.34e-07); LangChain `save_local`/`load_local` internals and pickle; the repo's full-document metadata (26.3 M characters); the storage table's sqlite-vec/Chroma/LanceDB rows; weights-sha256 vs revision.

### 7. Verify notebook plan

`study/notebooks/C3_index_verify.ipynb`, framework-free. Part A needs no key and no network. Part B runs from recorded Cohere responses (replay); it records once, when Yash chooses.

**Part A: offline (MiniLM-L6 `1110a243…` and L3 from the HF cache, `HF_HUB_OFFLINE=1`).** It recomputes the lesson's numbers from Corpus D, with small functions written in the notebook (it does not import `c3_measure.py`):

| Recomputed | Expected (C3_FACTS) | Chart (Plotly) |
|---|---|---|
| 97 records, `params_hash 1ca9c5a3b548`, offsets round-trip 97/97 | S1 | — |
| 7 single-field changes → 7 new hashes; `hash()` differs across two processes; the broken 2-field hash shares 92 ids, 89 with different text | S2 | — |
| Key sensitivity, now for **10** fields (adds `output_dimension`, `embedding_type`, `truncate`, `max_tokens`) | new; each must change the key | — |
| Page-10 edit: 0/97 ids kept, 1 miss; model switch: 0 hits; text-only key: 97 stale hits, D-002 evidence rank 3 → 16 | S4 | cache-hit bars per event |
| L3 unnormalised top-4 kept for 7/34 queries | S5 | norm histogram (L6 vs L3) |
| `vectors.npy` 149,120 B; manifest; loader refusals | S6, S7 | — |
| 16-change rebuild table | S7 | identity grid heatmap |
| Token counts per chunk under MiniLM's own tokenizer for 1000/200, 1500/300, 2000/400 on the **PyMuPDF snapshot** | re-measure: 07 D.6's figures (max 182; 4/65 and 32/65 over 256) came from PyPDFLoader text, so they may differ | histogram with the 256 line |
| Two cached MiniLM snapshots: weights sha256 equal, README differs | §1 | — |

Runtime: about 1–2 minutes on the CPU (two small models embed ~100 texts several times; S9 measured 1.8–6.3 s per cold embed of 97 texts, machine-specific).

**Part B: Cohere `embed-v4.0` (replay; recorded once through `llmops.cache`, Corpus D text only).** Every request sends `output_dimension`, `embedding_types=["float"]` and `truncate` explicitly.

| Call group | Calls | What it settles |
|---|---|---|
| 97 chunks, `search_document`, 1536, float, END | 2 (96 + 1) | raw norms (UNVERIFIED today), dim, `billed_units.input_tokens` total → tokens per character on this corpus, `meta.warnings` |
| The same first 8 chunk texts as `search_query` | 1 | how far query and document vectors of one text differ (lab Task 8's open question) |
| 10 seed questions (06 §6.7, drafts) as `search_query`, 1536 | 1 | top-4 per question for the 1536 index |
| 97 chunks + 10 questions at `output_dimension=256` | 3 | top-4 overlap 256 vs 1536; cosine between the server's 256 vector and the first 256 floats of the 1536 vector renormalised (is it a Matryoshka prefix? UNVERIFIED now) |
| Limit probe: two synthetic texts built by repeating Corpus D pages to about 6,000 and 10,000 tokens, `truncate=NONE` | 2 | an error on the second and not the first means the effective limit is near 8,192 (API figure); no error means at least 10,000 (consistent with 128k). Resolves E-C3-2 |
| Canary baseline: 3 fixed Corpus D sentences, cache bypassed, `record` samples 0 and 1 | 2 | the canary tolerance (Foundation §8.4) |

Total to record: **11 calls**, about 97 × 2 + 10 × 2 + 8 + 3 × 2 texts plus two long probes. Trial-cap impact: 11 of 1,000 calls/month. Price: **UNVERIFIED** ([C3-2]); the notebook prints "cost if called" from `prices.json` once a price is recorded. Replay runtime: seconds.

### 8. Apply-it tool plan and real-world checklist

`study/tools/index_integrity_check.py`: "Is my index trustworthy, and does it need a rebuild?" Standard library + numpy (+ the model's tokenizer from the HF cache for C10). No API call by default.

- **Inputs:** `--index <folder>` (the three files), optional `--config run.yaml` (06 §2.4 shape), `--snapshot` or `--docs` (to re-check offsets), `--cache .cache/emb` (to recompute keys), `--sample 5`, `--reembed none|local|cohere` (`cohere` goes through `llmops.cache`, so it is a replay hit after the first run; at most ⌈sample/96⌉ = 1 call), `--report report.md`.
- **Outputs:** a Markdown report (sections: manifest, files, rows, provenance, duplicates, model identity, truncation, rebuild verdict, checklist), a JSON summary, and an exit code (0 OK, 1 WARN, 2 REBUILD, 3 REFUSE) so CI can call it.

**Real-world checklist (12):**

| # | Check | Auto / manual | How |
|---|---|---|---|
| C1 | Manifest complete: snapshot, docs, parser, chunker, `params_hash`, embedding block **incl. `output_dimension`, `embedding_type`, `truncate`**, `embed_hash`, library versions, files | auto | key set vs a JSON schema (`jsonschema` installed) |
| C2 | Hash round-trip: sha256 of both files = manifest; `params_hash` = hash of the manifest's chunker block; `embed_hash` recomputed | auto | recompute |
| C3 | Rows: float32, shape (N, d), N = lines in `chunks.jsonl`, d = manifest dim, no NaN/inf | auto | numpy |
| C4 | Unit rows (± 1e-5) when `normalize: true` | auto | `np.linalg.norm` |
| C5 | Records: `text_sha256` recomputed; id = `doc:snapshot:params:seq05`; ids unique; `seq` never assumed equal to the row | auto | recompute |
| C6 | Provenance: `doc_text[char_start:char_end] == text`; pages inside the document's page range | auto with `--snapshot`/`--docs`, else manual (open 3 random chunks in the PDF) | slice and compare |
| C7 | Orphans: records whose `doc_id` is not in the manifest, manifest docs with no chunks, unreferenced cache files (info only) | auto | set differences |
| C8 | Duplicates: equal `text_sha256`; near-duplicate pairs with cosine ≥ 0.98 (count + top 5 pairs) | auto (the threshold is a judgement: manual review of the pairs) | V·Vᵀ on ≤ 5,000 rows |
| C9 | Mixed models: (a) every row's recomputed cache key is in the cache and its cached vector equals the row; (b) re-embed `--sample` rows with the manifest model: cosine ≥ 0.9999 (local) or ≥ the canary tolerance (Cohere); (c) a bimodal norm histogram before normalisation, if raw norms were recorded | auto | (a) needs `--cache`, (b) needs `--reembed` |
| C10 | Truncation rate: chunks whose token count under the model's tokenizer exceeds its limit (MiniLM exact); for Cohere, the byte bound (UTF-8 bytes ≤ limit ⇒ safe, assumption) plus billed tokens from the build trace | auto (MiniLM), partial (Cohere) | tokenizer from the HF cache |
| C11 | Rebuild needed? Compare manifest with `--config`: reasons `snapshot`, `chunker`, `embedding` (document side only); estimate misses and calls from the cache | auto with `--config` | the lesson's `rebuild_reasons` |
| C12 | Safety and hygiene: no pickle files in the folder; `.npy` loads with `allow_pickle=False`; no `meta` value longer than 2× its chunk (catches the full-document-in-metadata bug); model id still listed by the provider | auto, except the last (manual: Cohere models page, dated) | file scan; length ratio |

**Recommendation logic:**
1. C2, C3, C5 or C9 fails → **REFUSE**: the folder is corrupt or mixed; rebuild it from `chunks.jsonl` through the cache (cheap: only true misses are embedded).
2. Else C11 lists a reason → **REBUILD**, with the reasons and the estimated calls (⌈misses/96⌉).
3. Else C4 fails → **RE-NORMALISE**: rewrite `vectors.npy` from the cache; no API call.
4. Else C8, C10 or C12 warns → **WARN** with the fix: deduplicate, lower `chunk_size` below the token limit, move long `meta` out.
5. Else **OK**: print `index_manifest_hash` for the trace.

### 9. LLMOps notebook plan

`study/llmops/notebooks/C3_index_llmops.ipynb` (path as the Foundation's helper package decides). Foundation §12 row "2 · C3–C4": Cohere embed through `CachedEmbeddings`; trace embed hits/misses and retriever spans; retrieval metrics; embed cost; `embed_hash` versioning; retrieval regression. C3 has **no LLM step**, so no Groq or Claude call.

**Framework build (comparison only; the plain-Python index stays the system of record):**

| Framework piece | Lesson step | Hidden default to name |
|---|---|---|
| `CachedEmbeddings(provider="cohere", model="embed-v4.0", output_dimension=1536, embedding_type="float", truncate="END")` (Foundation §9.3) | steps 2–4: key, embed misses, batch 96 | LangChain `CohereEmbeddings` would send `truncate=None` (server END), no batching, `max_retries=3` (Foundation §9.2); `langchain-cohere` conflicts with cohere 7.2.0, so it is shown read-only |
| `InMemoryVectorStore(embedding=…)`, `add_documents(docs, ids=[chunk_id…])` | step 5 (without a manifest) | ids default to `uuid4` (pass ours); all texts go to one `embed_documents` call; `dump` saves no model identity; ties ordered by `argsort` |
| `vs.as_retriever(search_kwargs={"k": 4})` | C4's top-k (bridge) | `k=4` default; `similarity` search; filter is a pre-filter callable |
| A small `ManifestedStore` wrapper (notebook cell) | step 6, fail closed | shows what the framework lacks: refuse on a manifest mismatch |

**Caching and calls.** Every embed goes through `llmops.cache` (Foundation §2). The notebook **reuses the verify notebook's recorded keys** (same requests), so it needs no new calls for chunks and seed questions. New: the canary (3 texts, 1 call per scheduled run, `record` mode). It runs fully in `replay` with no key; a miss raises `ReplayMiss` with the command to record it.

**Tracing** (JSONL by default, Phoenix locally, LangSmith only for Corpus D after `privacy.assert_corpus_is("D")`; Foundation §3):
- Embedding span: provider, model, `input_type`, `output_dimension`, `embedding_type`, `truncate`, texts, batches, cache hits/misses, `billed_units.input_tokens`, `meta.warnings`, latency (misses only), cost if called, key prefix.
- Index-build span: `snapshot_id`, `params_hash`, `embed_hash`, sha256 of `manifest.json` (= `index_manifest_hash` in every later trace), rows, dim, build time cold vs warm.
- Retriever span: ranked `chunk_id`, page, score, rank (OpenInference `retrieval.documents`); exported spans carry ids and scores only.

**Dataset and evaluators.** Dataset = the 06 §6.7 draft seeds (10 items, learner-verified first), replaced by the frozen golden set when M1 exists, mirrored to LangSmith only as Corpus D. Evaluators are all code-based (`code-based-evaluators`): (1) the tool's C1–C12 as pass/fail evaluators on the index; (2) **parity**: identical top-4 ids between our NumPy index and `InMemoryVectorStore` over the same vectors (ties excepted); (3) retrieval Hit@4 and MRR per question (CE@4 once M2 builds it). No LLM judge (D-10). Retrieval and answer quality stay separate: C3 reports retrieval and integrity only.

**Experiment against the previous version.** v0 has no predecessor, so the comparison arms are: (a) Cohere 1536 vs the MiniLM fallback index (D-03's planned second model), and (b, Full) Cohere 256 vs 1536. Same records, same `params_hash`, same questions; only the embedding block differs (06 §4.1 rule 1). Report Hit@4/MRR per arm, rows, `vectors.npy` bytes, embed calls and build time.

**Cost, latency and tokens.** Calls per full build = ⌈97/96⌉ = 2; per batch of offline questions ⌈q/96⌉; online one call per query. Tokens from `billed_units.input_tokens`. Cost per build = tokens × price (**price UNVERIFIED**, so the column stays empty until `prices.json` has a dated price). Latency: p50/p95 of embed calls on misses only; build time cold vs all-hits (S9 analogue).

**Prompt and config versioning.** No prompt. The embedding block (10 key fields) lives in the run's `config.yaml`; `embed_hash` and `params_hash` name the folder; `index_manifest_hash` joins traces to the index; `prices.json` version is recorded with costs.

**Monitoring and feedback.**
- Embedding canary before each experiment and weekly: alert if min cosine to the recorded baseline drops below the tolerance (Foundation §8.4).
- On every commit (T1, offline): `index_integrity_check.py --config` on the current champion index; a retrieval regression on cached embeddings (identical top-4 for the dev seeds).
- On the monitor page (Foundation §8.3): cache hit rate, `ReplayMiss` count, Cohere `warnings`, truncation count (alert > 0), manifest drift.
- A failure (e.g. a mixed index, a canary drift) goes to the error-analysis log, then becomes a regression fixture (`ci-cd-evals`, `error-analysis`).

**Place in the lifecycle.** Analyze: read integrity reports and embed traces (`llm-observability`, `error-analysis`). Measure: parity, hit rate, Hit@4/MRR (`code-based-evaluators`, `rag-evaluation`). Improve: fix the key, manifest or normalisation (`evals-foundations`). dev (notebook) → CI (T1 integrity + retrieval regression; `replay` run of the notebook) → monitoring (canary, monitor page) (`ci-cd-evals`).

### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version (pin a released version ≥ 2 weeks old) | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Vectors, exact search, `.npy` files | `numpy` | 2.5.3 (keep) | yes | yes | — | BSD-3-Clause (plus bundled permissive licences) | yes |
| Default embedder (API) | Cohere `embed-v4.0` via `cohere` | SDK 7.2.0 (keep); model id from `.env` `COHERE_EMBED_MODEL_ID` | yes | no (replay yes) | ⌈N/96⌉ calls per build (Corpus D: 2); verify notebook 11 calls once; price **UNVERIFIED**; trial cap 1,000 calls/month, 2,000 inputs/min | MIT (SDK); service terms | yes (D-03). Use `ClientV2`, batch at 96 ourselves, `max_retries=0` |
| Fallback embedder (local) | `sentence-transformers/all-MiniLM-L6-v2` @ `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` via `sentence-transformers` | 6.1.0 (keep) | yes (model in HF cache) | yes | $0 | Apache-2.0 (library; model card says apache-2.0) | yes (D-03) |
| Second local model for the normalisation demo | `sentence-transformers/paraphrase-MiniLM-L3-v2` @ `4ca70771…` | cached | yes | yes | $0 | Apache-2.0 (UNVERIFIED for this card; not re-opened) | yes |
| Token counts for the truncation check | `transformers` / `tokenizers` (MiniLM's WordPiece) | 5.19.0 / 0.23.2 (keep) | yes | yes | — | Apache-2.0 | yes |
| Manifest schema check (tool C1) | `jsonschema` | 4.26.0 (keep) | yes | yes | — | MIT | yes |
| Run config | `pyyaml` | 6.0.3 (keep) | yes | yes | — | MIT | yes |
| Charts | `plotly` | 7.1.0 (keep) | yes | yes | — | MIT | yes |
| Exact-index comparison (P5, optional) | `faiss-cpu` | 1.15.1 | no | yes | — | MIT | optional; not needed for C3 |
| Single-file store with SQL filters (R2/D3 candidate) | `sqlite-vec` | 0.1.9 | no | yes | — | MIT / Apache-2.0 | **later, needs a decision in R2**; pre-1.0 |
| Not recommended | `chromadb` 1.5.9; `lancedb` 0.39.0; `hnswlib` 0.8.0 | — | no | yes | — | Apache-2.0 | no: hidden defaults / 103 MB / no Windows wheel |
| LLM per task | none: C3 has no generation or grading step | — | — | — | 0 LLM calls | — | yes (Groq and Claude start at C5) |
| Framework comparison store | `langchain-core` (`InMemoryVectorStore`, `Embeddings`) | 1.6.6 | no | yes | — | MIT | yes, LLMOps notebook only (D-32) |
| Graphs | `langgraph` | 1.2.12 | no | yes | — | MIT | **not needed** for C3 (a linear build) |
| Reading the repo's FAISS wrapper | `langchain-community` | 0.4.2 | no | yes | — | MIT | read-only; do not install for C3 |
| Official Cohere integration | `langchain-cohere` 0.6.0 | — | no | — | — | MIT | **conflicts** (needs cohere < 6); use `CachedEmbeddings` (Foundation §9.3) |
| Hosted tracing | `langsmith` | 0.14.4 | no | SDK yes; service no | `LANGSMITH_API_KEY`; free plan | MIT | yes, Corpus D only |
| Local tracing | `arize-phoenix-otel` + `openinference-instrumentation-langchain` (viewer: `uvx arize-phoenix@20.19.0 serve`) | 0.17.2 / 0.1.78 | no | yes | — | Apache-2.0 (server ELv2) | yes |
| Plain JSONL trace + cache | `study/llmops/` (Foundation §10) | plan | no | yes | — | ours | yes; C3's cache code moves there with its key extended (E-C3-1) |
| Tests / CI | `pytest`; `pre-commit`, `nox` (Foundation) | 9.1.1; 4.6.2; 2026.8.17 | pytest yes | yes | — | MIT / Apache-2.0 | yes |

Install lines (**not run**):

```text
# lesson, verify notebook, apply-it tool: nothing new
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4 arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78   # same pins as Foundation §11
uv add --group compare faiss-cpu==1.15.1      # optional, only if P5 wants a FAISS comparison
# sqlite-vec==0.1.9: only after an R2/D3 decision
```

**Keys:** `COHERE_API_KEY` (present; needed only to record the 11 verify calls and the canary); `LANGSMITH_API_KEY` optional; nothing for replay. Heavy items: none (LanceDB at 103 MB is the one to avoid).

### 11. Open questions for Yash (preferences only)

1. Should the index folder change when only the **query** `input_type` changes (today's `embed_hash`), or only for document-side settings? (Recommended: document side only; the query setting stays in the manifest.)
2. Default `output_dimension` for the Cohere index: keep **1536** (the server default, recommended) or try 256 as a Full-only arm?

---

## Concept C4: Dense retrieval
### 1. Sources checked
**Book pages (opened 2026-10-17, PyMuPDF text of each page read):**

| Page | What it holds (paraphrase) | Used for |
|---|---|---|
| Ch1 p.8/14 | Step 6: the question is embedded by the same process as the chunks, so distances mean something. Step 7: nearest chunks; a typical setup keeps the top 2 to 5 | Query side; the k range (verified: the "2 to 5" sentence is on p.8, not p.9) |
| Ch1 p.9/14 | Figure: one query dot, three nearest chunks highlighted. Step 8 (generation) | Visual; no scores shown |
| Ch1 p.10/14 | Query sketch: embed, search top-K, fetch text, generate | No score step |
| Ch1 p.12/14 | Questions whose evidence is scattered: retrieving only two or three chunks misses most of it | The recall side of k (MC-005) |
| Ch6 p.1/14; App p.13/23 | The asymmetry problem: short questions and long declarative chunks embed far apart | Why `input_type` / query prefixes exist |
| Ch11 p.2/13 | When the distance between question and chunk is large, a weaker chunk can outscore the right one | Distractors |
| Ch12 p.6/14, p.7/14 | Vector retriever returns top-K **with** similarity scores; retrievers' scores sit on different scales | Scores kept; scales not comparable |
| Ch13 p.2/13 | Embedding similarity is a rough proxy for relevance | Score ≠ relevance |
| Ch13 p.10/13 | Rerank pool K = 10–30, keep N = 3–5 | Link to R3 only |
| Ch20 p.1/11, p.4/11 | Grey-zone queries: cosine scores look reasonable while the chunks lack the answer; similarity ≠ relevance | No raw-score threshold |
| Ch22 p.4/19 | Precision@K shows the noise the retriever adds | P@k in the k sweep |
| Ch22 p.11/19, p.12/19 | Four noise types; distracting noise (similar but wrong) is the most dangerous; an **unsourced** "holds to about 50% noise, then collapses" claim with a sketch figure | Distractors; checked against [C4-5] |
| App p.20/23, p.22/23 | Glossary: Redundancy Problem; Top-K Retrieval (highest similarity scores, prone to redundancy) | Definitions |

**Repo (pinned `009adba2be1bef49780ef73b6dd3c18fd24b035b`, HEAD checked; cells 0-based, each opened):**

| Cell / line | Content checked |
|---|---|
| `simple_rag.ipynb` cell 10 | `encode_pdf`: PyPDFLoader, `RecursiveCharacterTextSplitter(1000, 200, length_function=len)`, FAISS with OpenAI embeddings |
| `simple_rag.ipynb` cell 13 | `as_retriever(search_kwargs={"k": 2})` |
| `simple_rag.ipynb` cell 15 | `retrieve_context_per_question` + `show_context`; no score printed |
| `helper_functions.py` L129–L149 | L143 `chunks_query_retriever.get_relevant_documents(question)`; L147 `[doc.page_content for doc in docs]` (scores, pages dropped); docstring L136–L139 promises a tuple with URLs, L149 returns a list |
| `json_rag.ipynb` cells 21–23 | `IndexFlatL2`; markdown: same model, L2 distance, lower is better; `model.encode([query_text])` without normalising, `NUM_NEIGHBORS = 5` |
| `multi_faceted_filtering.ipynb` cells 10, 12 | MiniLM in Chroma; `similarity_search_with_relevance_scores(query, k=10)` prints scores |
| `dartboard.ipynb` cell 13 | the query is embedded with `embed_documents` (wrong side for asymmetric models) |
| `dartboard.ipynb` cell 23 | the query is embedded with `embed_documents` again (so P4 D.8's "cell 23" and C4 G.2's "cell 13" are both right) |

**Existing course files audited:**
- `concepts/C4_dense_retrieval.md` (712 lines, Parts A–M; strong: D.1 query side, D.2 ties, D.3 score table, D.4 distractors, D.5 score ≠ relevance, D.6 toy k sweep; L items R-01…R-03, A-01…A-04, T-01).
- `labs/C4_dense_retrieval_lab.ipynb` (46 cells, Tasks 1–9, CHECK fingerprints; Task 8 Cohere off by default).
- `sources/verification/C4/C4_FACTS.md` (S1–S9, S-src, LT; run 2026-10-08, MiniLM only), `c4_measure.py`, `c4_sources.py`.
- Bridges read: `concepts/P4_embeddings_similarity.md` D.5 (wrong model), D.8 (input types and prefixes); `concepts/P5_vector_search.md` D.2–D.3 (argpartition, ties), D.5 (LangChain FAISS hidden defaults); `concepts/P6_ir_metrics.md` D.2–D.7 (headings: P/R/Hit, MRR, nDCG, CE preview).
- No `study/reading/C4_*.md`, no `study/questions/C4_questions.md` yet.

**AE book (paraphrase only):** AE Ch7, 'Precision@k and Recall@k' (k depends on question type; in the first stage, missing evidence is worse than noise); AE Ch2, 'Retrieval Fundamentals' (start from a keyword baseline). Not used for anything else.

**Interview repo (MIT, "Copyright (c) 2026 Om", @ `e080df2`), `04-rag-and-retrieval/questions.md`:**
- Q6 (bi-encoder at retrieval time; key limitation; says cosine scores rank but are not calibrated) → **candidate C4 interview item** (free: not in the seed bank).
- Q15 (query/document prefixes and task instructions) → candidate, but it fits P4 D.8 at least as well; only one of P4/C4 should take it.
- Q46 (triage of a wrong answer: was the gold chunk in the final prompt?) → fits C6 better.
- **Off limits for the kit:** Q11 (P4 hidden seed), Q48 vs Q50 (C4 hidden reserve, MC-005), `12-coding-challenges/08_semantic_search_rag.py` (P5 hidden seed). The ext-review C4 seed (AE Ch7 vs book Ch22 p.11/19) is also hidden.

**External sources (Source C; all opened 2026-10-17):**
1. **[C4-1]** Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering", EMNLP 2020. https://arxiv.org/abs/2004.04906 (v3) and https://aclanthology.org/2020.emnlp-main.550.pdf (full text read: §3, Table 2, §5.2, §5.4, App. C) — **verified**. = 01 §6 C#19.
2. **[C4-2]** Cohere, Embed API reference and Embeddings guide. https://docs.cohere.com/reference/embed (first 100k characters read), https://docs.cohere.com/docs/embeddings — **verified** (`input_type` required for v3+; values; 96 texts; `truncate` END). Unit-norm output: **not stated** (so UNVERIFIED). = C#52.
3. **[C4-3]** BGE and E5 model cards. https://huggingface.co/BAAI/bge-small-en-v1.5, https://huggingface.co/intfloat/e5-base-v2 (paper: Wang et al. 2022, https://arxiv.org/abs/2212.03533, not opened) — **verified** for the card statements (query instruction / prefixes; score ranges 0.6–1 and 0.7–1; relative order matters).
4. **[C4-4]** Liu et al., "Lost in the Middle: How Language Models Use Long Contexts", TACL. https://arxiv.org/abs/2307.03172 (v3 PDF text read, §5 and Fig. 11) — **verified**. = C#39. The Table 6 figure (75.8 → 53.8) is taken from the 2026-10-09 review's check, not re-read here.
5. **[C4-5]** Cuconasu et al., "The Power of Noise: Redefining Retrieval for RAG Systems", SIGIR 2024. https://arxiv.org/abs/2401.14887 (v4 HTML read) — **verified**.
6. **[C4-6]** AIQ `04-rag-and-retrieval/questions.md` Q6 (local copy @ `e080df2`, MIT) — **verified**.
7. **[C4-7]** OpenInference semantic conventions, https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md, and `openinference-instrumentation-langchain` `_tracer.py` (main) — **verified** (main branch, not the 0.1.78 tag).
8. **[C4-8]** langchain-core source: `libs/core/langchain_core/retrievers.py`, `vectorstores/base.py`, `vectorstores/in_memory.py` at https://github.com/langchain-ai/langchain (master) — **verified** (master, not the 1.6.6 tag).
9. C#18 SBERT semantic-search guide (symmetric vs asymmetric search, cited by 02) — **not re-opened** this session (UNVERIFIED here); [C4-1] to [C4-3] cover the same point.

### 2. Gap audit
Method: P3 gap audit. Ideas come from the book pages in §1, the C4 lesson (A–M), the lab tasks, the Part L items, the repo cells, MC-002/MC-005, and §5. "Studied?" is from `progress/concept_tracker.csv` (2026-10-17): P4, P5, P6, C3 are `not_started`; P1 is `exposed` (MC-001 open); C4 itself is `not_started`. "Written" never counts as studied.

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | The question is embedded by the **same model** as the chunks (MC-002) | Ch1 p.8/14; lesson A1, D.1; lab Task 1 | Yes (D.1) | C4 | No | core | Keep; open the lesson with it (the answer-first block) |
| 2 | **Query side vs document side**: asymmetric encoders (DPR's two encoders), Cohere `input_type`, E5/BGE prefixes; symmetric MiniLM | D.1, J3, lab 2b, Task 8 | Partly: D.1 has 2 lines; P4 D.8 has more but is not studied | C4 (P4 owns prefixes) | No | core | Short: one picture of two encoders feeding one score; the Cohere rule; "a wrong side raises no error". Full: DPR training ([C4-1]), prefixes ([C4-3]) |
| 3 | What an embedding is: a text → a fixed-length vector; "meaning space" | everywhere; Ch1 p.8/14 | No (P4 not studied) | P4 | No | bridge | Short: 3 sentences plus the 384/1536 dimensions of our two models |
| 4 | **Cosine, dot product, normalisation**; unit vectors make dot = cosine and L2 rank the same | D.1 "q × 3", K row 1, Gate 1→2 | **Missing in C4** (P4 D.2–D.3 not studied) | P4 | No | bridge | Short: a 3-d toy computed by hand (dot, norms, cosine); one line on L2. This closes the "similarity matrix" half of MC-002 |
| 5 | **Score vector (N,) vs similarity matrix** | MC-002; E table; lab CHECK 1 | Yes (E table, lab) | C4 | No | core | Keep; show the shapes (97,) and (10, 97) |
| 6 | **Exact top-k**: `V @ q`, `argpartition`, explicit sort | D.2 ("not repeated here, see P5") | **Missing** for this learner (P5 not studied) | P5 | No | bridge | Short: the three steps in 6 lines of NumPy; argpartition order is unspecified |
| 7 | Deterministic **tie rule** by `chunk_id`; zero-padded `seq` | D.2, A4, L A-03 | Yes | C4 | No | core | Keep; add that LangChain's `InMemoryVectorStore` has no tie rule ([C4-8]) |
| 8 | Reading a **score table**: gap 1–2, cut-off gap k/k+1, margin of the evidence below rank 1, absolute level | D.3, lab 3 | Yes | C4 | No | core | Keep; recompute with Cohere (E-C4-8) |
| 9 | **Distractor** kinds: near-duplicate (same text family) vs same-pattern (Kyoto "adopted in 1997") vs plain redundancy (exact copies, Ch15) | D.4, 02 card, R-03 | Partly: D.4 mixes "near-duplicate" and "same-pattern" under one name | C4 | No | core | Define the three; show D-002 rank 1 (same pattern) and rank 2 (near-duplicate) |
| 10 | **Score ≠ relevance**; not a probability; not comparable across models; only loosely across queries | D.5, J4, A-04; Ch13 p.2/13, Ch20 p.1/11 | Yes for models; across queries only implied | C4 | No | core | Add [C4-3] (BGE 0.6–1, E5 0.7–1 vs MiniLM ≈ 0 for unrelated) and the cross-query point (D-010 0.52 vs D-008 0.26) |
| 11 | **Hit@k** | D.1, D.6, E table | Incomplete: used before its one-line definition in E | P6 | No | bridge | Define in Short where first used, with the D-002 example |
| 12 | **CE@k** (all evidence groups covered) vs Hit@k | D.6, A3, MC-005 remediation | Incomplete (E table only) | P6 / M2 | No | bridge | Short: definition + D-007 (Hit@2 = 1, CE@2 = 0). Full: link 06 §7.2 |
| 13 | Precision@k | D.6 table | No | P6 | No | bridge | One line in the k section |
| 14 | MRR / rank sensitivity | J5 | No | P6 | No | next | Link to P6 |
| 15 | **Context tokens** and the tokenizer (`o200k_harmony`); tokens ≠ characters | D.6 | No (P1 exposed; MC-001 open) | P1 | Exposed only | bridge | One line plus a pointer; never "1,000 characters = 1,000 tokens" |
| 16 | **Choosing k, both sides** (MC-005) | D.6, A3, T-01 | Yes (toy sweep) | C4 | No | core | Keep; add [C4-4] Fig. 11 (accuracy saturates long before recall) and [C4-5] (distractors cost accuracy). Do **not** set the hidden-seed puzzle (E-C4-9) |
| 17 | Retrieval vs generation failure (evidence in top-k or not) | A5, J1–J4 | Yes | C4 / C6 / M5 | No | core | Keep; one table "CE@k = 0 → retrieval; CE@k = 1 and wrong answer → generation" |
| 18 | Index/embedder **compatibility**: model id, `embed_hash`, manifest | D.1, J2, lab 7 | Yes (D.1, J2) | C3 | No | bridge | Keep; one sentence on what C3 stores |
| 19 | Index files: `vectors.npy` row i ↔ `chunks.jsonl` line i; `seq` restarts per document | H.4 | Yes (H.4) | C3 | No | bridge | Full only |
| 20 | **Dense misses exact strings, codes, rare names** | not in the C4 lesson | **Missing** | P3 / R1 | No | bridge | Short: 2 sentences + DPR's qualitative finding ([C4-1]); one climate example (e.g. "CH4", "Kigali"); link R1 |
| 21 | Exact vs ANN search | not in the lesson | Missing (fine) | P5 | No | next | One line: 97 chunks, exact is instant; ANN in P5 |
| 22 | Bi-encoder vs cross-encoder (why dense is cheap) | not in the lesson | Missing (P4 D.7) | P4 / R3 | No | bridge | One sentence: chunk vectors are computed once; the query costs one embedding |
| 23 | Score ranges depend on training temperature | — | Missing | C4 (Full) | No | core (Full) | Full only, from [C4-3] |
| 24 | Normalise Cohere vectors yourself; check norms | D.1 says "normalising q does not change ranking" | Partly | C4 / C3 | No | core | Add: Cohere docs do not promise unit vectors ([C4-2]); assert norms |
| 25 | Chunk truncation before embedding (text past the limit cannot help retrieval) | not in C4 | Link only | P1 / C2 (07 D.6) | Exposed | next | One link |
| 26 | LangChain retriever API: `invoke`; no scores; default k = 4; threshold mode | H.2 Q3 | Partly (H.2) | C4 (LLMOps) | No | core (LLMOps notebook) | Lesson Full: one box "what a framework retriever hides"; the LLMOps notebook shows it |
| 27 | Distracting noise harms answers | D.4 (book Ch22 p.11/19) | Yes, as a book claim | X3 / V2 | No | next | Cite [C4-5] once; measuring it is C5/V |
| 28 | Lost in the middle (position) | — | — | P7 / X3 | No (MC-004 open) | next | Link only; do not mix with k |
| 29 | Abstention thresholds | D.5, J4 | Yes (as "not in v0") | V3 | No | next | Keep the "no threshold in v0" rule |
| 30 | Dedup / diversity (MMR) | K table | Link | X3 / R4 | No | next | Link |

**Result.** 4 ideas are **missing** for this learner (4 cosine/normalisation, 6 exact top-k, 20 dense vs exact terms, 22 bi-encoder cost), 6 are **incomplete** (2, 9, 10, 11, 12, 24), the rest are taught. Because P4, P5 and P6 are not studied, items 3, 4, 6, 11, 12 must be **taught in place in Short mode**, not linked.

### 3. Quiz coverage
**No `study/questions/C4_questions.md` exists.** The full lesson's Part L has 8 items (R-01…R-03, A-01…A-04, T-01). Checked against what a Short reading must contain:

| Part L item | Answerable from a Short version today? | Missing from Short |
|---|---|---|
| C4-R-01 (what happens to the question) | Yes, if Short keeps D.1 | "same dimension is not enough" needs the S7 number |
| C4-R-02 (why return scores) | Yes | — |
| C4-R-03 (near-duplicate distractor) | Partly | the cos 0.78 between rank 2 and the evidence is in FACTS S4, not in D.4's table (D.4 shows 0.72 for rank 1) |
| C4-A-01 (write `retrieve`) | **No** for this learner | exact top-k with `argpartition` + explicit sort (P5 not studied: gap 6) |
| C4-A-02 (k 4 → 8) | Yes | — |
| C4-A-03 (tie by hand) | Yes | — |
| C4-A-04 (0.5 threshold) | Yes | — |
| C4-T-01 (hospital leaflets, choose k) | Partly | CE@k definition (gap 12) and dedup as a later fix (link) |

**Question titles needed for the kit file** (new scenarios; none from the hidden seed bank or the AIQ reserves Q11, Q48, Q50):

| id | Type | Title |
|---|---|---|
| C4-PRE-01 | pre | Before any chunk gets a score, what happens to the question? |
| C4-PRE-02 | pre | Does a cosine of 0.46 mean the chunk is 46% relevant? |
| C4-R-01 | R | Which model and which side embed the question, and why does "same dimension" prove nothing? |
| C4-R-02 | R | One query gives a score vector of what shape, and why is that not a "similarity matrix"? |
| C4-R-03 | R | What is the difference between a near-duplicate distractor, a same-pattern distractor and an exact copy? |
| C4-R-04 | R | Why can't a raw score be compared across two embedding models? (BGE 0.6–1 vs MiniLM) |
| C4-R-05 | R (interview, `source=AIQ-04-Q6`) | Verbatim AIQ Q6: how a bi-encoder works at retrieval time and its key limitation |
| C4-A-01 | A | Compute dot product, both norms and the cosine for two 3-d vectors; does scaling q change the ranking? |
| C4-A-02 | A | Given 5 scores and ids, give the top-3 with the tie rule |
| C4-A-03 | A | Read a score table: the 1–2 gap, the cut-off gap and the evidence margin; which query is fragile? |
| C4-A-04 | A | From a small k sweep (Hit@k, CE@k, tokens), state both sides of moving k from 4 to 2 and to 8 |
| C4-A-05 | A (code) | Write `retrieve(question, embedder, V, chunks, k)` returning ranked dicts with float scores |
| C4-T-01 | T | A new corpus of product manuals full of part numbers: what would dense retrieval miss, and how would you show it? |
| C4-T-02 | T | A teammate swapped to a new embedding model and kept the old index and the old 0.4 threshold: list what breaks and the checks that catch it |
| C4-T-03 | T | Choose k for a new corpus with many near-identical sections, with a reason and a measurement plan (fresh scenario; the lesson's hospital item may stay as practice) |

Key points these need that a Short reading must teach: gaps 4, 6, 11, 12 and 20 of §2 (cosine by hand, exact top-k, Hit@k, CE@k, exact-term misses).

### 4. Errors found in existing material (not edited)
Reported only; nothing was edited.

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| E-C4-1 | 02 C4 card, Book line | "Ch1 p.8–9/14 (top-K, typically 2–5)": the 2-to-5 sentence is on **p.8** only; p.9 is the scatter figure (three nearest chunks) and Step 8 | Ch1 p.8/14 and p.9/14 text, opened 2026-10-17 | "Ch1 p.8/14 (top 2 to 5); p.9–10/14 (figure, query sketch: no scores)" |
| E-C4-2 | 02 C4 card, Book line; 04 C4 row | Both list only Ch1 pages. The lesson relies on Ch1 p.12/14 (small fixed k misses scattered evidence), Ch6 p.1/14 + App p.13/23 (asymmetry), Ch12 p.6–7/14 (scores, scales), Ch13 p.2/13 and Ch20 p.1/11, p.4/11 (similarity ≠ relevance), Ch22 p.11/19 (distracting noise) | Pages opened; lesson G.2 item 3 already reports this for 04 | Add these pages to both |
| E-C4-3 | 04 C4 row, Gap column | "'lower L2 = better' never explained": `json_rag.ipynb` cell 22 (markdown) explains it | Cell 22 opened | "Unexplained in `simple_rag`; explained in `json_rag` cell 22" (lesson G.2 item 1 agrees) |
| E-C4-4 | 02 C4 card ⚠ note "`get_relevant_documents` was removed in langchain-core 1.x" | **Confirmed, with precision.** `langchain_core/retrievers.py` (master, read 2026-10-17) defines no public `get_relevant_documents` and does not mention the name at all; public entry points are `invoke`/`ainvoke`, hooks `_get_relevant_documents`/`_aget_relevant_documents`. The lesson verified the same on 1.3.0 in the old venv; the runtime error type is still UNVERIFIED (expected `AttributeError`) | [C4-8] | Keep; add "use `retriever.invoke(question)`" |
| E-C4-5 | Foundation §9.2 row `VectorStoreRetriever` ("`similarity`, `k=4`") | Right but incomplete. `search_kwargs` defaults to `{}`; the k=4 comes from each store's `similarity_search(k=4)`. Three more hidden behaviours matter for C4: (a) the retriever returns **Documents without scores** on every path (the `similarity_score_threshold` path computes scores, then drops them); (b) `similarity_score_threshold` needs a float `score_threshold` but does not check 0–1, and the base `_select_relevance_score_fn` raises `NotImplementedError`, which `InMemoryVectorStore` does not override, so that search type fails on the in-memory store (read, not run: UNVERIFIED at runtime); (c) `InMemoryVectorStore` ranks with `argsort()[::-1]` and **no tie rule** | [C4-8] | Add (a)–(c) to the §9.2 table; the C4 LLMOps notebook must not use `similarity_score_threshold` |
| E-C4-6 | C4 lesson H.4 assumption 7 / 06 §2.4 | `.env` name `COHERE_EMBED_MODEL` vs 06's `COHERE_EMBED_MODEL_ID` (already recorded by the lesson and by 06's interface table) | Lesson H.4 | Still open; the C4 LLMOps notebook should read `COHERE_EMBED_MODEL_ID` with the old name as fallback |
| E-C4-7 | C4 lesson D.1, FACTS §3 | Cohere `input_type` effect "UNVERIFIED". Still true for our data. Externally, Cohere documents `input_type` as **required** for v3+ embed models (see §5 [C4-2]), so "query embedded as a document" is a real, silent risk, not a hypothetical one | [C4-2] | Keep UNVERIFIED for the size; make lab Task 8 a recorded run (≈ 20 cached calls) once Cohere credits allow |
| E-C4-8 | C4 lesson | No Cohere numbers anywhere: every score, gap and threshold example is MiniLM. v0's default embedder is Cohere `embed-v4.0` (D-03). Score levels, gaps and the D-010 comparison will differ | FACTS §0 | Re-measure S3–S7 with cached Cohere vectors (§7 plan); label MiniLM tables "fallback model" |
| E-C4-9 | C4 lesson Part A/D.6 vs kit rules | The ext review's C4 seed (book Ch22 p.11/19 "about half noise" vs AE Ch7 "missing evidence is worse") is a **hidden** transfer seed. The new lesson/reading must not put those two claims side by side as a puzzle | Ext review §3b; FORMAT.md "Hidden seeds" | Teach the evidence ([C4-4], [C4-5]) but not the reconciliation scenario |

### 5. What the research says
All of this is **external** (Source C). Study first, then our interpretation.

#### [C4-1] DPR: Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering", EMNLP 2020 (arXiv 2004.04906 v3; ACL Anthology PDF read)
- **The study.** Two separate BERT encoders, one for questions (E_Q) and one for passages (E_P); score = dot product of the two vectors (eq. 1). Trained on question–passage pairs with **in-batch negatives** (batch 128) plus one BM25 hard negative per question. Index: 21,015,324 Wikipedia passages of 100 words, FAISS HNSW. Five QA datasets: NQ, TriviaQA, WebQuestions, CuratedTREC, SQuAD. Metric: **top-k retrieval accuracy** = share of questions whose top k passages contain a span with the answer (that is our Hit@k, with "contains the answer string" as relevance).
- **The result** (Table 2, test sets, top-20): NQ 78.4 vs BM25 59.1; TriviaQA 79.4 vs 66.9; WQ 73.2 vs 55.0; TREC 79.8 vs 70.9; **SQuAD 63.2 vs 68.8 (BM25 wins)**. The gap is largest at small k. Fig. 1: 1,000 training questions already beat BM25 on NQ dev. Ablation (§5.2, App. B): L2 ≈ dot product, both **better than cosine**. Trained on NQ only and tested on WQ/TREC: 3–5 points below fine-tuned, still above BM25. Qualitative analysis: BM25 is sensitive to highly selective keywords; DPR handles lexical variation but may under-represent rare salient phrases. Cost: 995 questions/s with FAISS vs 23.7 for Lucene per thread, but the dense index took 8.8 h of 8-GPU encoding plus 8.5 h to build, against about 30 min for Lucene.
- **Limits.** Wikipedia factoid QA with short answers; "relevant" = answer string present (can be a lucky match); a supervised, in-domain retriever, not an off-the-shelf API model; SQuAD shows the lexical-overlap case where BM25 wins (the authors' conjecture: questions written while looking at the passage, and a skewed 500-article sample).
- **For this project.** (1) The query side is literally a **different encoder** in DPR: the clearest picture of why `search_query` ≠ `search_document` (MC-002 bridge). (2) Dense retrieval wins on paraphrase and loses on rare exact strings: the R1/P3 link, and why Corpus T's acronyms and codes need a check. (3) "Top-k accuracy" is Hit@k; for multi-fact items we need CE@k (06 §7.3). (4) The paper picks k = 20–100 for a reader model, not for an LLM prompt: its k says nothing about our k = 4. (5) Dot vs cosine: DPR trained for dot product; with unit vectors (our v0) they rank the same (P4 D.3).

#### [C4-2] Cohere Embed API reference and Embeddings guide (docs.cohere.com/reference/embed, /docs/embeddings; read 2026-10-17)
- **What it says.** `input_type` is **required for embedding models v3 and higher**; values `search_document` (vectors stored for search), `search_query` (queries run against them), `classification`, `clustering`, `image`. The guide tells you to embed the query with `search_query` and the passages with `search_document`. Max 96 texts per call; `truncate` default `END` (a silent cut; `NONE` raises an error instead); `output_dimension` exists only for embed-v4 and newer; `embedding_types` default `["float"]`. The guide's similarity example divides by both norms (cosine). **Neither page says whether vectors come back unit length.** The guide's examples now use `embed-v5.0-pro` (dimensions 256–2048), so a newer model than the course's `embed-v4.0` exists.
- **Limits.** Vendor documentation; no number for how much a wrong `input_type` costs.
- **For this project.** (1) Normalise Cohere vectors ourselves (06 §2.4 `normalize: true`) and assert unit norms; never assume. (2) The `input_type` mistake raises no error (P4 D.8, lesson J3): add a spy test, and record `input_type` in every embedding span and cache key (Foundation §2.3). (3) Record `truncate` (Foundation E2). (4) The model id stays in `.env`; moving to v5 would be a new index (`embed_hash`), never a silent swap.

#### [C4-3] Query prefixes and score ranges in open models: BGE and E5 model cards (huggingface.co/BAAI/bge-small-en-v1.5; huggingface.co/intfloat/e5-base-v2, which links Wang et al. 2022, arXiv 2212.03533; read 2026-10-17)
- **What they say.** BGE: add the instruction "Represent this sentence for searching relevant passages:" to **queries only**, mainly for short queries; v1.5 works without it with a "slight degradation". E5: the `query: ` / `passage: ` prefixes are required, or performance degrades; use `query: ` on both sides for symmetric tasks. **Both cards say their cosine scores bunch high** (BGE about 0.6–1; E5 about 0.7–1) because of a low contrastive temperature (0.01). Both say only the **relative order** matters; BGE says to choose any threshold from the score distribution on your own data.
- **Limits.** Model-card statements, not controlled studies; no size given for the prefix effect.
- **For this project.** The cleanest evidence that scores are not comparable across models: MiniLM gave −0.09 and −0.05 for unrelated pairs (P4 D.5), while BGE puts almost everything above 0.6. A 0.5 threshold means "quite similar" for MiniLM and "unrelated" for BGE. C4 D.5 should cite this, and the apply-it tool must warn whenever a fixed threshold is used.

#### [C4-4] Lost in the Middle: Liu et al., TACL (accepted 2023; arXiv 2307.03172 v3; PDF text read)
- **The study.** Multi-document QA on NaturalQuestions-Open with Contriever-retrieved distractors and the gold position varied; plus a case study "Is more context always better?": Contriever (fine-tuned on MS-MARCO) returns k = 5 to 50 documents, and retriever recall is compared with reader accuracy (Fig. 11) for six models.
- **The result.** Accuracy is highest with the evidence at the start or end and lower in the middle (U-shape; GPT-3.5-Turbo 75.8 → 53.8 in the 20-document table, as checked by the 2026-10-09 review). Fig. 11: reader accuracy saturates long before retriever recall; more than 20 documents adds only about 1.5% (GPT-3.5-Turbo) and about 1% (Claude-1.3) while the context grows a lot. The authors suggest reranking or retrieving fewer documents when appropriate.
- **Limits.** 2023 models; NQ factoid answers; "accuracy" = an annotated answer string appears in the output.
- **For this project.** Recall@k keeps rising with k, but answer quality does not follow. That is why C4 reports CE@k **and** context tokens, and why k is chosen by measurement (MC-005). Position effects belong to P7/X3 (MC-004); C4 only links them.

#### [C4-5] The Power of Noise: Cuconasu et al., SIGIR 2024 (arXiv 2401.14887 v4; HTML read)
- **The study.** NQ-open, 21M Wikipedia passages, Contriever retriever (FAISS `IndexFlatIP`), four instruct LLMs of 7B or less (Llama2, Falcon, Phi-2, MPT; 4-bit, greedy). "Distracting" = a high retriever score but no answer; "random" = sampled passages. Counts 0–18; positions near, mid or far from the gold passage.
- **The result.** Distractors hurt: Llama2 with the gold passage 0.5642 → 0.4283 with one distractor, 0.3748 with eight; mid position with 18 distractors 0.1795. Random passages sometimes **helped** (up to +35% relative in one setting), but the gain depends on the model (Falcon did not gain next to the gold passage) and on placement; the authors call the mechanism unexplained.
- **Limits.** Small, quantised 2024 models; string-match accuracy; the random-noise gain is not a recipe, and the authors do not recommend it for production.
- **For this project.** Our D-002 rank-1 Kyoto chunk (the same "adopted in <year>" pattern) is a "distracting" passage in this paper's sense. The paper is the measured version of the book's distracting-noise warning (Ch22 p.11/19). C4 reports distractors as a retrieval-side fact; whether Groq is misled by them is a C5/V-phase measurement.

#### [C4-6] Interview item: AIQ `04-rag-and-retrieval/questions.md` Q6 (MIT, "Copyright (c) 2026 Om", @ `e080df2`)
- **What it says.** A bi-encoder embeds the query and the document independently; documents are embedded once at index time; the document vector is fixed before the query exists, so token-level matching, rare terms and negation suffer; cosine scores are good for ranking but are not calibrated probabilities, and thresholds do not carry across models or domains. The fix is a cross-encoder rerank.
- **Check against our sources.** Consistent with [C4-1] (rare salient phrases), [C4-3] (score ranges) and P4 D.5 (negation pair 0.84). Usable as the C4 interview item: the verbatim question with the MIT notice, the repo answer only after the attempt.

#### Tooling sources (used in §9)
- **[C4-7] OpenInference semantic conventions** (github.com/Arize-ai/openinference, `spec/semantic_conventions.md`, main, read 2026-10-17): span kinds `RETRIEVER`, `EMBEDDING`, `RERANKER`; `retrieval.documents.N.document.{id, score, content, metadata}`; `embedding.model_name`. **The LangChain instrumentor** (`openinference-instrumentation-langchain`, `_tracer.py`, main): `_as_document` writes only `document.content` and `document.metadata`; it never sets `document.id` or `document.score`. So a LangChain retriever traced through OpenInference loses the ranked ids and scores unless we write them ourselves, and it **does** export the chunk text (privacy rule: corpus D only).
- **[C4-8] langchain-core source** (`retrievers.py`, `vectorstores/base.py`, `vectorstores/in_memory.py`, master, read 2026-10-17): see E-C4-4 and E-C4-5. In short: `invoke` only; `VectorStoreRetriever(search_type="similarity", search_kwargs={})` with the store's default k = 4; no scores on the returned Documents; `similarity_score_threshold` unsafe here; `InMemoryVectorStore` = cosine with `argsort()[::-1]`, no tie rule, `embed_query` for queries and `embed_documents` for documents. Version caveat: master, not the 1.6.6 tag the Foundation pins.

#### Current practice (2024–2026)
- Dense retrieval with a bi-encoder is the first stage, usually beside BM25 (hybrid, R1) and before a cross-encoder rerank (R3). AIQ Q6 and Q10 and the book's Ch12–13 agree.
- Hosted embedders expose query/document types (Cohere `input_type`); open models use prefixes or instructions ([C4-3]).
- Exact search is normal at our scale (97 chunks; D-07). ANN is P5's topic; link only.

#### Pitfalls, with evidence
1. Wrong model, same dimension: no error, Hit@4 8/8 → 3/8 (C4 S7).
2. Wrong side (`search_document` for the query): silent; size UNVERIFIED for Cohere ([C4-2]).
3. Fixed score thresholds: scores are model-specific ([C4-3]); D-010 scores 0.5196 with no answer, above 5 of 8 answerable seeds (C4 S4).
4. Near-duplicate and same-pattern distractors above the evidence: 4 of 8 seeds (C4 S4); they hurt answers ([C4-5]).
5. Exact strings, codes and rare names: dense under-represents them ([C4-1]; P3, R1).
6. Framework defaults: no scores, no tie rule, k = 4 by accident ([C4-8]).
7. Ties: `argpartition` order is unspecified (P5 D.3).

#### How to evaluate
Retrieval only, with the 06 §7.3 metrics on answerable items: **CE@k primary**, Hit@k and MRR as diagnostics, plus mean context tokens at each k. Baseline: v0 at k = 4 on the same `dataset_sha256`. Slice per category and by the near-duplicate tag (06 §7.6). Answer quality is a separate C5/M3 measurement; never fold the two together.

#### Interview questions (titles)
1. How does a bi-encoder work at query time, and what is its key limitation? (AIQ Q6)
2. Why do query/document prefixes or `input_type` matter, and what breaks silently if you ignore them? (AIQ Q15, if P4 does not take it)
3. Can a cosine threshold of 0.5 tell you "not found"?
4. How do you choose k?
5. The right chunk came back at rank 5 with k = 4: a retrieval or a generation failure?

### 6. Lesson blueprint
The new lesson (`study/lessons/C4_dense_retrieval.html`) follows the P3 order: answer first → theory in one read → formula sheet → steps → verify → apply → check. It reuses the existing lesson's measured facts (C4_FACTS S1–S9) and adds the Cohere re-measurement from §7 once it is recorded.

**Running example:** Corpus D (the climate PDF, 97 v0 chunks) and seed **D-002** "In what year was the Paris Agreement adopted?". Why this one: it shows everything at once: the evidence at rank 3, a same-pattern distractor at rank 1 (Kyoto, 1997), a near-duplicate at rank 2 (p.23 without the year), and a 0.00008 gap between ranks 3 and 4. A second query is used only where D-002 cannot show the point: **D-010** (no answer, high score) for "score ≠ relevance", **D-007** for Hit@k vs CE@k, and **D-008** ("Kigali", low absolute scores) for rare terms.

#### The answer first (draft, 5 sentences)
1. Dense retrieval turns the question into a vector with the **same embedding model** that turned every chunk into a vector, on the model's **query side**.
2. It then scores every chunk with one number, the cosine of the two vectors, and keeps the k highest, with a fixed rule for ties.
3. Those scores say how close a chunk is to the question in that model's space; they do not say whether the chunk holds the answer, and they cannot be compared across models.
4. So you keep the scores and read them: the gap between the top two, the gap at the cut-off, and lookalike chunks that rank above the real evidence.
5. The number k is a trade: a larger k brings in more of the evidence but costs tokens and adds distractors, so k is chosen by measuring complete evidence against context size, not by feel.

#### The theory in one read (12 linked ideas)
| # | Idea | Formula or rule | Short / Full |
|---|---|---|---|
| 1 | An embedding maps a text to a fixed-length vector (MiniLM 384, Cohere `embed-v4.0` 1536 by default) | `v = E(text)`, `v ∈ ℝᵈ` | Short |
| 2 | Same model, right side: chunks with `E_doc`, the question with `E_query`; symmetric models make them equal, asymmetric ones do not (DPR: two encoders; Cohere: `input_type`) | `q = E_query(question)`, `V[i] = E_doc(chunk_i)` | Short |
| 3 | Dot product and cosine; after normalising, they are equal; L2 then ranks the same way | `cos(q, v) = (q·v)/(‖q‖‖v‖)`; for unit vectors `‖q − v‖² = 2 − 2 cos` | Short (3-d hand example) |
| 4 | One query → one score per chunk: a vector, not a matrix | `s = V q`, shape (N,) | Short |
| 5 | Exact top-k: partition, then sort, with a tie rule | `argpartition(−s, k−1)[:k]`, then sort by (−s, `chunk_id`) | Short |
| 6 | Read the score table: gap 1–2, gap k/k+1, the evidence margin, the absolute level | `gap_i = s₍ᵢ₎ − s₍ᵢ₊₁₎`; `margin = s₍₁₎ − s(first relevant)` | Short |
| 7 | Distractors: same-pattern, near-duplicate, exact copy | `cos(chunk_a, chunk_b)` between chunk vectors to flag lookalikes | Short |
| 8 | A score is not relevance, not a probability, and is model-specific (MiniLM unrelated ≈ 0; BGE ≈ 0.6–1) | none; a rule: no fixed threshold in v0 | Short |
| 9 | Hit@k and CE@k | `Hit@k = 1[∃ i ≤ k: rel(c_i)]`; `CE@k = 1[every evidence group covered by top-k]` | Short |
| 10 | Choosing k: CE@k rises with k (never falls); tokens grow about linearly; precision falls; readers saturate early ([C4-4]); distractors cost answers ([C4-5]) | `tokens(k) ≈ Σ_{i≤k} t_i`; `P@k = #rel/k` | Short (sweep table); Full (studies) |
| 11 | Dense is weak on exact strings and rare names; BM25 is strong there | — | Short (2 sentences + one example); link R1 |
| 12 | Compatibility: a vector from another model has the same shape and no error, but the scores are noise | assert `embedder.model_id == manifest.model_id` (or `embed_hash`) | Short |

#### Formula-sheet items
`cos(q, v) = q·v / (‖q‖‖v‖)` · unit vectors: `cos = q·v`, `‖q − v‖² = 2 − 2 cos` · `s = V q` (N,) · `top-k = sort_{(−s, id)}(argpartition(−s, k−1)[:k])` · `gap_i`, `margin` · `Hit@k`, `CE@k`, `P@k = #rel/k` · `tokens(k)` · the tie rule · the compatibility assert · Cohere: chunks `search_document`, questions `search_query`.

#### Step-by-step outline (D-002 on Corpus D)
1. **The failure** (no scores): `simple_rag.ipynb` cell 15 → `helper_functions.py` L147 drops the scores; with the repo's `k=2` (cell 13), D-002 on our v0 index would lose its evidence (rank 3, C4 S3).
2. **Bridge: vectors and cosine** with a 3-d hand example; normalise, show dot = cosine; scale q by 3 and the ranking stays.
3. **Embed the question** with the index's model, query side. Shapes q (d,), V (97, d), s (97,). Show the wrong-model case (Hit@4 8/8 → 3/8, no error).
4. **Top-k**: argpartition + sort + tie rule; the shuffled-duplicate example (C4 S5).
5. **The D-002 score table** (ranks 1–5, scores, pages, "holds the year?"), then the four readings (gaps, margin, level).
6. **Distractors**: Kyoto (same pattern, rank 1), p.23 paragraph (near-duplicate, rank 2); cosine with the evidence chunk 0.72 (rank 1) and 0.78 (rank 2) (C4 S4).
7. **What a score cannot tell you**: D-010 (no answer) beats 5 of 8 answerable seeds; the BGE/E5 score ranges; a 0.5 threshold fails both ways.
8. **Exact terms**: one rare-term query (D-008 "Kigali") with its low absolute scores; when to add BM25 (R1).
9. **Choosing k**: the sweep table (Hit, CE, P@k, tokens at k = 1, 2, 4, 8), both sides in one sentence; the studies in one paragraph each (Full).
10. **What a framework retriever hides**: `invoke` returns Documents with no scores; default k = 4; no tie rule (Full box).
11. **Hand-off to C5**: the ranked dict (H.4) and the trace form without text.

#### Visuals (each earns its place)
| Visual | What it shows |
|---|---|
| Two-encoder diagram (SVG): question → E_query → q; chunks → E_doc → V; one dot product per chunk | MC-002: the query is embedded, and the result is one score per chunk, not a matrix |
| 3-d vector sketch with an interactive "scale q" slider | Cosine and ranking do not change when q is scaled; the raw dot does |
| D-002 score ladder (horizontal bars, ranks 1–8, the k = 4 cut line, relevant bars marked) | The evidence at rank 3, the tiny 3–4 gap, the large 4–5 gap |
| Score-range strip: MiniLM, Cohere (once recorded), BGE/E5 ranges from the cards (labelled "model card, not measured") | Why thresholds do not travel across models |
| k-sweep chart: CE@k and Hit@k (left axis) against mean context tokens (right axis), k = 1…8 | Both sides of k in one picture (MC-005) |
| Retrieval-vs-generation decision table | CE@k = 0 → fix retrieval; CE@k = 1 and wrong answer → fix generation |

#### Full-only
DPR's training (in-batch negatives, hard negatives; L2 ≈ dot > cosine in their ablation) · why low contrastive temperature pushes scores high ([C4-3]) · the studies on k ([C4-4], [C4-5]) with their limits · LangChain internals ([C4-8]) · the index row-alignment rules (H.4) · the repo-wide score-API scan · per-seed tables S4 and the P5-vs-v0 chunking difference (S2).

### 7. Verify notebook plan
**File:** `study/notebooks/C4_dense_retrieval_verify.ipynb`, the same shape as `P3_bm25_verify.ipynb`: one section per lesson section, each with "what this verifies", the code, and a `check(name, got, expected)` line against C4_FACTS. Framework-free (NumPy, sentence-transformers, tiktoken, Plotly). Data: Corpus D (the climate PDF), the v0 chunker (07 H.1/H.3 spans, 97 chunks, `params_hash` `1ca9c5a3b548`), the 10 draft seeds of 06 §6.7 (labelled `llm-draft`: a demo, never a result).

| § | Recomputes | Source of truth | Arm |
|---|---|---|---|
| 1 | The 3-d toy: dot, norms, cosine, L2² = 2 − 2cos; scaling q by 3 keeps the ranking | arithmetic | none |
| 2 | Index rebuild: 97 chunks, `chunks.jsonl` sha256 `d4108b89…`, V (97, 384), unit norms (max dev 1.19e-07) | FACTS S1 | MiniLM |
| 3 | D-002: shapes, top-8 table, gaps 0.00931 / 0.01269 / 0.00008 / 0.09978; the rank-1 record | FACTS S3 | MiniLM |
| 4 | 10-seed summary (first relevant rank, first CE, rank-1 score, gaps); 28 of 70 adjacent gaps < 0.01 | FACTS S4 | MiniLM |
| 5 | Distractors: the four outranked seeds and their chunk-to-evidence cosines; D-003 mirror | FACTS S4 | MiniLM |
| 6 | Ties: duplicated + shuffled index → [69, 166, 68, 165]; the two wrong orders | FACTS S5 | MiniLM |
| 7 | k sweep: Hit, CE, Group-Recall, P@k, mean tokens (`o200k_harmony`) at k = 1, 2, 4, 8; Plotly dual-axis chart | FACTS S6 | MiniLM |
| 8 | Query side: symmetric MiniLM (1.15e-07), wrong model L3 (Hit@4 3/8, no error), q × 3 | FACTS S7 | MiniLM + L3 (both cached locally) |
| 9 | **New: score ranges.** Histogram of all 97 scores per seed, per model; a "threshold sweep" showing that no single cut separates D-009/D-010 from the answerable seeds | new numbers → new FACTS rows | MiniLM; Cohere (replay) |
| 10 | **New: the Cohere arm.** Sections 3–8 again with `embed-v4.0` vectors: D-002 table, seed summary, k sweep; plus `input_type` right vs wrong (queries as `search_document`): Hit@4, CE@4, rank of the evidence, max abs difference between the two query vectors; raw norms before normalising | closes E-C4-7, E-C4-8 and the lesson's UNVERIFIED Task 8 | Cohere (replay) |
| 11 | **New: the exact-term probe.** For each seed, the query tokens that look like identifiers or rare names (P3 tokenizer; idf above the 90th percentile) and the dense rank of the first chunk containing them (substring), vs the BM25 rank | new FACTS rows | MiniLM, Cohere; `rank_bm25` |
| 12 | **New: framework parity (read-only cell, skipped if `langchain-core` is absent).** `InMemoryVectorStore` over the same vectors returns the same top-4 ids as our `retrieve` for the seeds without ties, and a different order on the duplicated index (no tie rule) | [C4-8] | MiniLM |

**External calls (all through the Foundation's `llmops` cache; the notebook runs in `replay` mode):**
- Cohere `embed-v4.0`, recorded once: 97 chunks as `search_document` (2 calls: 96 + 1, the API limit is 96 texts per call), 10 seed questions as `search_query` (1 call), the same 10 as `search_document` (1 call). **4 calls, 117 texts**, about 16k input tokens (97 chunks × median 162 tokens, FACTS S6). Price per token **UNVERIFIED** (Foundation §6.2); the trial key's 1,000 calls/month is not a constraint.
- The C3 index's Cohere vectors are reused if C3's cache already holds them (same key: provider, model, `input_type`, dimension, `truncate`, preproc, text), so only the 2 query calls are new.
- No LLM call. Groq is not needed.

**Offline:** yes for every MiniLM section (HF cache, `HF_HUB_OFFLINE=1`). The Cohere sections run from the recorded pack; with no pack they print "ReplayMiss: record with `LLMOPS_CACHE_MODE=record`" and are skipped, never fail silently. **Runtime:** not measured; expected short (97 chunks, about 120 short embeddings for MiniLM on CPU, plus model loading). Measure it when the notebook is built and write it into the notebook header.

**What it must not do:** build or show a solution to the lab tasks before an attempt (the lab stays blank-file first); state any Cohere number in the lesson before it is recorded in FACTS.

### 8. Apply-it tool plan and real-world checklist
**Tool:** `study/tools/dense_retrieval_check.py` ("does dense retrieval work on MY documents and questions, and can I trust its scores?"). Same shape as `bm25_fit_check.py`: a CLI plus `run_check()` / `render_report()` for import; writes one Markdown report; no LLM call.

**Inputs**
- `--index <dir>`: a C3 index folder (`vectors.npy`, `chunks.jsonl`, `manifest.json`), **or** `--docs a.pdf b.md …` to build one with the v0 chunker (07 recursive 1000/200, per page).
- `--questions q.jsonl` (or `.txt`): `{"id", "q", "type"?, "expect"?, "evidence"?}`. `expect` = a short string the right chunk contains (as in `bm25_fit_check`); `evidence` = 06 §6.1 `evidence_groups` for CE@k when Yash has labelled spans.
- `--embedder minilm|cohere` (default from the manifest). Cohere goes through `llmops` (default mode `replay`; `--record` to call). `--k 4`, `--ks 1,2,4,8`, `--dup 0.90` (chunk-to-chunk cosine that flags a near-duplicate), `--tokenizer o200k_harmony`.

**Outputs** (Markdown report + a JSON sidecar for the monitor page)
1. **Setup and compatibility:** embedder id vs manifest `model_id` / `embed_hash`; dimensions; vector norms (min/max); `input_type` used for documents and queries.
2. **Per question:** the top-(k+2) table (rank, chunk id, page, score, gap to next, "contains `expect`?"), plus the margin of the first relevant chunk below rank 1, and flags: `NEAR-TIE` (gap 1–2 < 0.01), `EDGE` (gap k/k+1 < 0.01), `TIE` (|Δ| < 1e-6 inside the top k+1, with the tie rule applied), `DISTRACTOR` (a chunk ranked above the first relevant one), `NEAR-DUP` (two top-k chunks with cosine ≥ `--dup`, or text Jaccard ≥ 0.8), `LOW-LEVEL` (rank-1 score in the bottom quartile of this run's rank-1 scores).
3. **Query-side check:** each question embedded on both sides; max abs difference and whether the top-k changes (symmetric model: identical; Cohere: reported, from the cache).
4. **Exact-term check:** identifier-like or rare query tokens (P3's tokenizer rules); the dense rank of the first chunk containing them vs the BM25 rank (`rank_bm25`, P3 settings).
5. **Score ranges:** rank-1 scores of all questions; if any question is marked `"type": "unanswerable"`, the overlap between its rank-1 score and the answerable ones, and the message "no single threshold separates them" when they overlap.
6. **k sweep** (only with `expect` or `evidence`): Hit@k, CE@k (with `evidence`), P@k and mean context tokens at each k; the smallest k that reaches the CE plateau; a Plotly HTML chart beside the report.
7. **Checklist and recommendation** (below).

**The real-world checklist (12 checks)**
| # | Check | How | Auto/manual |
|---|---|---|---|
| D1 | Query and index use the same model (id or `embed_hash`) | compare with the manifest | auto |
| D2 | Queries use the query side (`search_query` / prefix) and chunks the document side | spy on the embedder calls; read the manifest's `input_type` | auto |
| D3 | Vectors are unit length (so cosine = dot) | norms within 1e-3 of 1 | auto |
| D4 | Scores are returned and kept for every result | the retriever output has a float `score` per rank | auto |
| D5 | Ties are broken by a fixed rule, not by row order | re-run on a shuffled copy; identical order | auto |
| D6 | Near-ties at the top: how many questions have gap 1–2 < 0.01 | count `NEAR-TIE` | auto |
| D7 | The cut-off is fragile: how many have gap k/k+1 < 0.01 | count `EDGE` | auto |
| D8 | Near-duplicate chunks fill the top k | count `NEAR-DUP`; list the pairs | auto |
| D9 | A distractor outranks the evidence | count `DISTRACTOR` (needs `expect`/`evidence`) | auto |
| D10 | Exact strings and codes are found by dense retrieval | exact-term check: dense rank vs BM25 rank | auto |
| D11 | No fixed score threshold is used anywhere downstream | search your code/config for a numeric cut on raw scores; this tool only warns | manual |
| D12 | k is chosen from CE@k against tokens on labelled questions, not by feel | k sweep present and the chosen k at the plateau | auto when labels exist, else manual ("label 10 questions first") |

**Recommendation logic** (first match wins)
1. D1, D2 or D3 fails → **fix the setup first** (re-embed or re-index); every other number is meaningless.
2. D4 or D5 fails → **fix the retriever output** (keep scores; tie rule).
3. D10 fails on 2 or more questions, or for more than 20% of questions with identifiers → **add BM25 (hybrid, R1)**.
4. D9 or D8 on more than 25% of labelled questions → **keep k, consider reranking (R3) or dedup (X3)**; report which.
5. D12 shows CE@k still rising at the largest k → **raise k or fix chunking (I1)**; if CE is flat from a smaller k → **lower k** (tokens saved, reported).
6. Fewer than 10 labelled questions → **"not enough labels to choose k"**: show the table, decide nothing.
7. Else → **dense retrieval at this k looks fine for these questions** (a mechanism check, not an evaluation).

The thresholds (0.01, 0.90, 20%, 25%, 10) are **assumptions** to be tuned on Corpus D and T; the report prints them. Example output: `study/tools/examples/climate_dense_report.md` built from the 10 seeds (MiniLM, offline), like P3's `climate_report.md`.

### 9. LLMOps notebook plan
**File:** `study/notebooks/C4_dense_retrieval_llmops.ipynb`. It applies Foundation §12 row "2 · C3–C4" (Cohere embed through `CachedEmbeddings` + a retriever; embed hits/misses and retriever spans; retrieval metrics; embed cost; `embed_hash`; retrieval regression). Studied **after** the lesson, lab and verify notebook. No LLM call: C4 has no generation.

#### Framework build: pieces mapped to the mechanism
| Mechanism step (lesson) | Framework piece | Note / hidden default |
|---|---|---|
| Embed chunks (document side) | `llmops.lc.CachedEmbeddings.embed_documents` → Cohere `search_document` | Foundation §9.3 adapter; batches at 96; records `truncate`, dimension (E2) |
| Embed the question (query side) | `CachedEmbeddings.embed_query` → `search_query` | the side the repo gets wrong in `dartboard.ipynb` cells 13 and 23 |
| Score + top-k + tie rule + keep scores | **`CourseDenseRetriever(BaseRetriever)`**: a 40-line class over the C3 index (`vectors.npy`, `chunks.jsonl`, `manifest.json`) that calls the lesson's `retrieve` and returns `Document`s with `id=chunk_id` and `metadata={rank, score, page, char_start, char_end, embed_hash}` | Chosen route. Asserts the manifest model id on load |
| (comparison, read-only cell) | `InMemoryVectorStore.from_texts(..., embedding=CachedEmbeddings)` + `.as_retriever()` | Shows the defaults the lesson warns about: `search_type="similarity"`, k = 4 from `similarity_search`, Documents **without scores**, `argsort()[::-1]` with **no tie rule**. Re-embedding the chunks is all cache hits |
| Never | `search_type="similarity_score_threshold"` | Needs a float `score_threshold`; on `InMemoryVectorStore` the base `_select_relevance_score_fn` raises `NotImplementedError` (read, not run); thresholds on raw scores are wrong anyway (D.5) |
| Call | `retriever.invoke(question)` | `get_relevant_documents` no longer exists ([C4-8]) |

FAISS and Chroma are not used (D-07: NumPy exact); `langchain-community` is not needed.

#### Tracing (LangSmith and the local option)
- **Always: the JSONL trace** (06 §2.5 `candidates.dense`: rank, `chunk_id`, `doc_id`, page, offsets, score; no text) via `llmops.trace`.
- **Spans** (Foundation §3.3, OpenInference names [C4-7]): `EMBEDDING` (provider, `embedding.model_name`, `input_type`, dimension, n texts, cache hit/miss, latency, billed units) and `RETRIEVER` (`retrieval.documents.N.document.id` = `chunk_id`, `.score`, `.metadata` = rank, page, `embed_hash`; k; index manifest hash). **Write these spans ourselves**: the LangChain OpenInference instrumentor sets only `document.content` and `document.metadata`, never `document.id` or `document.score` ([C4-7]), and it exports chunk text.
- **Local viewer:** Phoenix (`uvx arize-phoenix@20.19.0 serve`), spans exported by `llmops.trace` through `arize-phoenix-otel`. Phoenix's hide flags (`OPENINFERENCE_HIDE_RETRIEVAL_DOCUMENTS` etc., Foundation §3.1) for anything that is not corpus D.
- **Hosted:** LangSmith only inside `tracing_context(enabled=True)` after `privacy.assert_corpus_is("D")`; never on Yash's own documents (the apply-it tool never exports).

#### Dataset and evaluators
- **Dataset:** until M1 freezes `D_eval_v1.x`, the 10 draft seeds (`llm-draft`, 06 §6.7), loaded with `llmops.datasets` and tagged "demo"; mirrored to LangSmith only as a corpus-D dataset with `upload_results=False` runs. After M1: the frozen D dev split.
- **Evaluators (code only; no judge, D-10):** Hit@k, **CE@k** and Group-Recall@k (the `contracts_check.py` reference `rel`/`ce`), MRR@10, P@k, mean context tokens (`o200k_harmony`), plus run-level invariants: every result has a float score; scores sorted descending; ties by `chunk_id`; unit norms; query embedded with `search_query`; embedder id = manifest id. Wrapped in the LangSmith/Phoenix evaluator signature by `llmops.evals` (Foundation §10).

#### Experiment against the previous version
There is no earlier version: C4 builds v0's retrieval stage. The notebook compares **arms of v0's retrieval** on identical comparison keys (`dataset_sha256`, `snapshot_id`, qids, `scorer_version`):
1. Cohere `embed-v4.0` (default, D-03) vs MiniLM (fallback);
2. Cohere query as `search_query` (right) vs `search_document` (wrong);
3. k = 2, 4, 8 at the default embedder (CE@k vs mean context tokens).
With 8 answerable draft items every difference is a **demo**, reported with n and no verdict; the real comparison waits for the frozen eval set (M2, M4).

#### Cost, latency and tokens
- Cohere calls, texts and billed units per arm; cost-if-called from `prices.json` (Cohere embed price **UNVERIFIED**, Foundation §6.2); cost paid = 0 in replay.
- Latency p50/p95, named method (06 §7.5): query embedding (from recorded `latency_ms`, cache hits excluded) and NumPy scoring + top-k (local, measured live).
- Context tokens per k (the cost side of retrieval; feeds C5's prompt budget).

#### Prompt and config versioning
No prompt. Versioned items: the config `retrieval:` block (`method: dense`, `similarity: cosine_exact`, `k`, `tie_rule: chunk_id`), `embed_hash`, `index_manifest_hash`, `retriever_version` (the class's version string), all hashed into `config_hash` (Foundation §7). An arm = a one-variable config diff.

#### Monitoring and feedback
- **Embedding canary** (Foundation §8.4): 3 fixed strings with the cache bypassed in `record` mode on a schedule; alert if the vectors drift beyond the tolerance from two runs.
- **Score-distribution drift:** median and IQR of rank-1 scores, and the `NEAR-TIE` / `EDGE` / `NEAR-DUP` rates from the apply-it tool's JSON sidecar, per run on the monitor page; alert on a shift beyond a tolerance set from the first two runs (a silent model change moves the whole distribution).
- **Replay misses** and Cohere error classes (402, 429; Foundation §2.5).
- **Feedback:** a question where a distractor beat the evidence, or an exact-term miss, goes to the error-analysis log (M5 bucket "retrieval: ranking" or "retrieval: lexical"); once confirmed it becomes a golden item tagged `near-duplicate-distractor` or `exact-term` and a T1 regression case.

#### CI (the retrieval regression test, T1)
`tests/test_c4_retrieval.py`, no network: (1) seed fingerprints with MiniLM computed locally (`78ebfed94d0021da` for D-002's top-4, C4 S9) and, when the replay pack exists, the same for cached Cohere vectors; (2) CE@4 and MRR ≥ champion − tolerance on the frozen set (06 §9.6); (3) two runs give identical rankings; (4) the shuffled-duplicate tie test; (5) a spy test that `embed_query` was used; (6) the manifest guard raises on a wrong model. **Injected regressions** that must fail: ascending sort, query on the document side, scores dropped, `np.float32` scores (the lab's broken variants, C4 LT).

#### Its place in the lifecycle, and the skills used
| Part | Lifecycle | Skill |
|---|---|---|
| Score tables, distractor and exact-term flags read per query | Analyze | `error-analysis`, `trace-data-analysis` |
| Hit@k, CE@k, MRR, tokens per arm; retrieval kept apart from answers | Measure | `rag-evaluation`, `code-based-evaluators` |
| k, embedder and `input_type` arms | Improve (demo only at v0) | `improving-llm-agents` |
| JSONL + spans, Phoenix, LangSmith (corpus D) | dev | `llm-observability` |
| T1 regression + injected failures | CI | `ci-cd-evals` |
| Canary and score-drift panels | monitoring | `ci-cd-evals`, `evals-foundations` |

**External calls:** Cohere embed only; the same 4 recorded calls as the verify notebook (identical cache keys), so **0 new calls** if the verify notebook was recorded first. Runs fully in `replay` with no key.

### 10. Tools, frameworks, libraries and LLMs
C4 needs **no new library** for the lesson, lab, verify notebook or apply-it tool. The LLMOps notebook uses only packages the Foundation already lists (pins from Foundation §11, PyPI checked there on 2026-10-17). "Installed" is from `uv pip list` (read-only, 2026-10-17).

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Vectors, scores, exact top-k | `numpy` | 2.5.3 (keep) | yes | yes | — | BSD-3 | yes (D-07: NumPy exact) |
| Default embedder | Cohere `embed-v4.0` via `cohere` | SDK 7.2.0 (keep); model id from `.env` | yes | no (API); yes in replay | 4 recorded calls (117 texts, ≈ 16k tokens) for verify + LLMOps; price UNVERIFIED | MIT (SDK) | yes (D-03) |
| Fallback embedder | `sentence-transformers/all-MiniLM-L6-v2` (snapshot `1110a243…`) via `sentence-transformers` | 6.1.0 (keep) | yes (model in HF cache) | yes | $0 | Apache-2.0 | yes |
| Wrong-model demo | `sentence-transformers/paraphrase-MiniLM-L3-v2` (snapshot `4ca70771…`) | — | yes (HF cache) | yes | $0 | Apache-2.0 | yes |
| Optional score-range demo | `BAAI/bge-small-en-v1.5` | revision to pin at download | **no** (not in the HF cache; download size UNVERIFIED) | after download | $0 | MIT (model card) | optional; the model-card ranges suffice without it |
| Exact-term comparison | `rank-bm25` | 0.2.2 (keep) | yes | yes | — | Apache-2.0 | yes |
| Context tokens | `tiktoken` (`o200k_harmony`) | 0.14.0 (keep) | yes | yes (encoding cached) | — | MIT | yes |
| Charts | `plotly` | 7.1.0 (keep) | yes | yes | — | MIT | yes |
| Tests | `pytest` | 9.1.1 | yes (dev) | yes | — | MIT | yes |
| LLM | **none**: C4 makes no LLM call. Groq `openai/gpt-oss-20b` and Claude are not needed (C5 owns generation) | — | — | — | $0 | — | yes |
| Framework core (`BaseRetriever`, `Document`, `InMemoryVectorStore`) | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (D-32, LLMOps notebook only) |
| Graphs | `langgraph` | — | — | — | — | — | **not needed** for C4 (a linear step) |
| Provider packages | `langchain-cohere` | — | — | — | — | — | **not used** (needs cohere < 6; the `CachedEmbeddings` adapter replaces it, Foundation decision 1) |
| Community stores | `langchain-community` (FAISS, Chroma) | — | — | — | — | — | **not needed** (D-07); the repo's FAISS is reading only |
| Hosted tracing | `langsmith` | 0.14.4 | no | SDK yes; service no | free plan; corpus D only | MIT | yes |
| Local tracing client | `arize-phoenix-otel` | 0.17.2 | no | yes | — | Apache-2.0 | yes |
| Instrumentor (optional) | `openinference-instrumentation-langchain` | 0.1.78 | no | yes | — | Apache-2.0 | optional: it drops ids and scores ([C4-7]); our own spans are the default |
| Local trace viewer | `arize-phoenix` (server, via `uvx`) | 20.19.0 | no | yes | — | ELv2 | yes, outside the lock |
| Cache / replay / trace helpers | `study/llmops/` (Foundation §10) | plan | no | yes | — | ours | yes; **a prerequisite** for the Cohere arm |

**Install lines (do not run; the same as Foundation §11, nothing C4-specific):**
```text
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4
uv add --group llmops arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78   # instrumentor optional
uvx arize-phoenix@20.19.0 serve                                                                   # on demand
```

**Keys:** `COHERE_API_KEY` (present) only to **record** the 4 Cohere calls; none for replay. `LANGSMITH_API_KEY` (+ `LANGSMITH_ENDPOINT`) only if the LangSmith mirror is used. `.env` model name: `COHERE_EMBED_MODEL_ID` (06) or the older `COHERE_EMBED_MODEL` (E-C4-6). Nothing heavy: no GPU, no server except the optional Phoenix viewer.

### 11. Open questions for Yash (preferences only)
1. **Record the Cohere arm** (4 embed calls, about 117 texts, once) as soon as the LLMOps helper exists, so the lesson can show Cohere scores instead of MiniLM only? **Yes** is recommended.
2. **Download `BAAI/bge-small-en-v1.5`** (not in your HF cache) for a measured "scores bunch high" chart, or keep the model-card ranges as labelled quotes? **Keep the quotes** is recommended (no download needed).

---

## Concept C5: Context construction and answer generation with citations

### 1. Sources checked

**Book pages (opened 2026-10-17 from PyMuPDF text of the PDFs; paraphrased).**

| Page | What is on it | 02/04 claim | Verdict |
|---|---|---|---|
| Ch1 p.9/14 | Step 8: retrieved chunks plus the question go to the model; the answer should rest on the documents, not on training memory | 02: "grounded generation" | Correct |
| Ch1 p.10/14 | Query algorithm sketch, steps 5–6: pass question + chunks; answer grounded in the context | 04: Ch1 p.9–10/14 | Correct |
| Ch3 p.6/14 | Hallucination check: even with perfect context a model can add claims absent from the sources; "useful chunk?" vs "faithful answer?" are different questions | not in 02/04 | Needed (D.7 of the lesson already uses it) |
| Ch3 p.8/14 | Hallucination-check algorithm, then Step 5 "Highlight Source Segments": a model finds verbatim supporting excerpts with document references, like footnotes | 02/04: "source highlighting" p.8–9 | Correct |
| Ch3 p.9/14 | Source-highlighting algorithm: return segments with document IDs and source references | 02/04 | Correct |
| Ch3 p.10/14 – p.11/14 | Model choice for verification: small model for binary grading steps, a mid-size model for highlighting, the most capable for final generation; 2–4 extra calls per query; "I don't know" beats a confident wrong answer | not in 02/04 | **Add**: it is the book's own model-tier argument (§6 idea 9) |
| Ch19 p.8/10 | Attribution works **after** generation; explainable retrieval explains **why** a document was retrieved | not in 02/04 | Needed (explanation ≠ attribution) |
| Ch22 p.5/19 | Generation prompts weight documents that come **first** (the book's only position claim; no source) | not in 02/04 | Bridge to lost-in-the-middle (P7 D.6 already uses it) |
| Ch22 p.7/19 – p.8/19 | Faithfulness = supported claims / total claims; isolates generation from retrieval | 04 M3 row | Next (M3, V1) |
| Appendix p.5/23 | Credits **Ch19** with making each claim cite its source | — | Inconsistent with Ch19 p.8/10 (already noted in C5 G.1) |
| Appendix p.9/23 | Again credits **Ch19** with "the citation trail" for legal work | — | **New**: a second instance of the same inconsistency, not in C5 G.1 |
| Appendix p.21/23 | Glossary "Source Attribution" → Chapters 3 and 19 | — | Consistent with Ch3 |

Not in the book: an inline citation format, a parser, cited ⊆ retrieved, malformed tags, the word "abstain", reasoning-token budgets, `finish_reason`, structured (JSON) citation output, citation precision/recall as named metrics, or position effects beyond Ch22 p.5/19.

**Repo cells (`RAG_Techniques` @ `009adba`, 0-based; opened with a JSON reader 2026-10-17).**

| Cell | Verified content | Note for C5 |
|---|---|---|
| `reliable_rag.ipynb` 18 | System line "Answer the question based upon your knowledge"; `ChatGroq(model="llama-3.1-8b-instant", temperature=0)`; docs wrapped as `<docN>` with Title/Source; **has 1 saved output** (an answer with no citations) | 02 card correct. The C5 verification log says only cell 23 has saved output: wrong, cell 18 has one too |
| `reliable_rag.ipynb` 22 | `HighlightDocuments` Pydantic model (`id`, `title`, `source`, `segment` lists); `PydanticOutputParser`; `mixtral-8x7b-32768`; "exact match" demanded in the prompt, never checked | 02 card correct. A **structured** (JSON) citation pattern, done as a second call (Ch3 p.8/14) |
| `reliable_rag.ipynb` 23 | Prints `ID: doc3` + segment; saved output | — |
| `local_rag_huggingface_faiss.ipynb` 22 | Context-only prompt with a fixed refusal sentence; no citation request | Good contrast for the abstention string |
| `local_rag_huggingface_faiss.ipynb` 24 | `format_docs` writes `[Page {doc.metadata.get('page','?')}]` headers; LCEL `{context, question} \| prompt \| llm \| StrOutputParser()` | Page labels exist, never cited. The loader is `PyPDFLoader` (cell 12), whose `page` metadata is 0-based (**UNVERIFIED** here; see §4 E-C5-4) |
| `local_rag_huggingface_faiss.ipynb` 26 | `ask()` keeps text after the last `Answer:`; 4 test queries incl. an out-of-scope one; no saved output | 02 card's "cell 26 (`ask`)" correct. 04 cites 24, 28 instead; both are needed |
| `local_rag_huggingface_faiss.ipynb` 28 | `RunnableParallel(answer=rag_chain, sources=retriever)`; prints "Sources used" from a second retriever run | "Sources" = retrieved, not cited (C5 B.1) |
| `crag.ipynb` 20 | `retrieve_documents` returns `page_content` only; `generate_response` asks to append sources with links | Local path cannot cite a page |
| `helper_functions.py` L162–L205 | `create_question_answer_from_context_chain` (context-only prompt + `with_structured_output(QuestionAnswerFromContext)`), `answer_question_from_context` | No citation handling (04 row wrong to list it under C5; C5 G.2 already says so) |

**Existing course files audited:** `concepts/C5_generation_citations.md` (Parts A–M, 679 lines; Part L has 3 R, 4 A, 1 T items); `labs/C5_generation_lab.ipynb` (9 tasks, `FakeGroq`, Task 9 Groq optional and never run); `sources/verification/C5/` (`C5_FACTS.md`, `c5_measure.py`, `c5_sources.py`, outputs: 127 source checks pass, lab 8/8 CHECK + 34/34 broken variants); `concepts/P7_grounded_prompting.md` D.1–D.8 (the template parts, budget, lost in the middle, permissive prompt); 06 §2.4, §2.5, §3.1, §3.3, §7.4; ext review §3a rows 4–6; no `study/reading/C5_*` or `study/questions/C5_*` file exists.

**AE book:** not opened for C5. The method parts C5 needs (code-based checks first, separate retrieval and generation metrics, human labels before any judge) come through the project skills `code-based-evaluators`, `rag-evaluation`, `evals-foundations`, `llm-observability` (read; paraphrased below), which cite the AE book. Full AE treatment belongs to M3/V1.

**Interview repo** (`ombharatiya/AI-Engineer-Interview-Questions`, MIT, "Copyright (c) 2026 Om"; quoting allowed with this notice):

| Item | Use in C5 |
|---|---|
| `04-rag-and-retrieval/questions.md` Q28 "How do you make a RAG system produce trustworthy citations?" | Core interview item. Its answer has three layers (prompt/format, verification, UX), says "mechanically validate that every cited ID exists in the provided set - free", and names Anthropic's Citations API |
| `03-prompt-engineering-and-context/questions.md` Q30 "You have retrieved chunks and a question. How do you actually build the prompt? …" | Prompt assembly; recommends edge placement (lost in the middle) and doc ids after each claim |
| `08-inference-and-production/questions.md` Q14 (`finish_reason` / `stop_reason` never checked) | Already used for the `length_stop` flag (ext review §3a row 5) |
| `02-llm-fundamentals/questions.md` Q44 "lost in the middle" | Bridge only |
| `12-coding-challenges/08_semantic_search_rag.py` (prompt assembly with `[1]`, `[2]` anchors) | Coding drill: rewrite it to `[doc:page]` + subset check |

**External sources (numbered; details in §5).**
- [C5-1] Groq docs: Reasoning, Structured Outputs, API reference (chat completions) — verified 2026-10-17
- [C5-2] Anthropic, Citations (platform.claude.com) + `claude-api` skill — verified 2026-10-17
- [C5-3] AI-Engineer-Interview-Questions 04 Q28 (MIT) — verified (local pinned copy)
- [C5-4] Gao et al. 2023, ALCE (EMNLP) — verified (arXiv abstract + HTML body, first ~78%)
- [C5-5] Cohere docs: RAG with documents; RAG citations — verified 2026-10-17
- [C5-6] Liu et al. 2023, Lost in the Middle (TACL) — verified (abstract only; bridge)
- [C5-7] langchain-community `PyPDFParser` source (main) — verified
- UNVERIFIED items: Groq behaviour at the cap and real `finish_reason` values; whether `reasoning_tokens ≤ completion_tokens` on Groq; size of the Anthropic Citations input overhead; Cohere `command-a-plus-05-2026` availability; Groq rate-limit plan for gpt-oss-20b.

### 2. Gap audit

Tracker (2026-10-17): C5 `not_started`; **P7 `not_started`** (MC-003, MC-004 open); C4 `not_started`; P1 `exposed` (MC-001 open). So every P7 idea that C5 relies on is a **bridge that must be taught inside C5**, even though the current lesson says "C5 does not repeat that".

| # | Idea | Used where | Taught before use? | Owner | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Index time vs query time: overlap is fixed at indexing; the prompt only arranges existing chunks (**MC-003**) | C5-A1, C5-A-01 (MC-003 check item), D.1 | P7 D.1; C5 D.1 one line | P7 | No | bridge | Short: the two-row diagram (index row / query row) at the top, with "nothing is re-chunked at query time" in a callout. MC-003 closes only through C5-A-01 + P7 items |
| 2 | Parts of a grounded prompt (source-only rule, citation rule, fixed refusal sentence, no outside knowledge, support rule, numbered blocks, question last) | D.2 template file; every check depends on rules 1–2 | P7 D.2; C5 says it does not repeat | P7 | No | bridge | Short: one annotated template (06 §3.3) with each rule mapped to the flag that checks it (rule 1 → `no_citation`/`uncited_sentence`; rule 2 → abstention match; rule 3 → support, not checked in v0) |
| 3 | Prompt token budget: W − output reserve − margin ≥ fixed + Σ blocks | C5-A-03 (input 7,552 → 7,808), C5-A-04 (802 → 1,442), apply-it check | P7 D.4 | P7 | No | bridge | Short: the 3-line budget formula and the 802-token D-002 split (107 / 695; sources 680) |
| 4 | Reasoning tokens share the output cap; empty answer at 12 (O2) | D.3 assert, D.6 `length_stop`, C5-A3, C5-R-03 | P1 B.2 | P1 | Exposed (MC-001 open) | bridge | Short: one sentence + the O2 example; already there |
| 5 | `max_completion_tokens` replaces deprecated `max_tokens`; Groq default 1,024 "may be too low" | D.3, K, lab Task 2 CHECK, 06 §2.4 | **Incomplete** (K keeps `max_tokens`) | C5 | No | core | Teach the new name, keep `max_tokens` only as the trace field; config change recorded (Foundation E3) |
| 6 | `reasoning_effort` omitted → server default `medium` | D.3 | Yes (D.3) | C5 | No | core | Keep |
| 7 | Groq returns reasoning text in a separate `reasoning` field (`include_reasoning`); never parse citations from it | parser input; trace storage | **Missing** | C5 | No | core | Short: one line in D.3 ("parse `message.content` only"); Full: store or drop the field, and why (size, privacy) |
| 8 | `finish_reason` values and the `length_stop` / `unexpected_finish_reason` flags | D.6, C5-A-03 | Yes (D.6, added 2026-10-09) | C5 | No | core | Keep |
| 9 | Reasoning tokens counted twice? `reasoning_tokens ≤ completion_tokens`; cost = input × p_in + completion × p_out | cost per query, apply-it tool, ext review §3a row 6 | **Missing** (row 6 not applied) | C5 (cost owned by D2) | No | core | Short: one CHECK line + the cost formula with Foundation §6.2 prices |
| 10 | Rank-sorted numbered blocks with `[i] (doc_id:page)` headers | D.2, C5-A-01 | Yes | C5 | No | core | Keep |
| 11 | Template file + `template_sha256` + rendered `prompt.sha256` | D.2, H.3 | Yes | C5 | No | core | Keep; link Foundation §7 (prompt files never edited after first use) |
| 12 | Strict citation grammar; malformed tags reported, not repaired | D.4 | Yes | C5 | No | core | Keep |
| 13 | Page → chunk resolution; cited ⊆ retrieved; retrieved-but-not-used | D.5, C5-A2, C5-A-02 | Yes | C5 | No | core | Keep |
| 14 | Exact abstention sentence after normalising | D.6, C5-A4 | Yes (bridge from P7 D.7) | C5/P7 | No | core | Keep |
| 15 | What the subset check misses: support (T19) | D.7, C5-R-02 | Yes | C5 → V1 | No | core | Keep |
| 16 | Citation precision / recall (ALCE definitions; 06 §7.4) and why C5's checks are their free necessary conditions | D.7, J5, quiz criteria name "citation precision" | **Incomplete** (named, never defined) | M3/V1 | No | bridge | Short: two one-line definitions + "invalid citation ⇒ precision 0 for that citation; uncited sentence ⇒ recall 0 for that sentence". Full: ALCE's NLI step and its κ |
| 17 | Retrieval vs generation failure (CR-11) and **context swapping** | Part J, lab Task 7 | Part J yes; context swapping **missing** | M5 / `rag-evaluation` | No | bridge | Short: one paragraph: feed the gold chunk, re-ask; still wrong = generation |
| 18 | Lost in the middle (**MC-004**) | J4 (gold at rank 3 of 4 ignored) | P7 D.6 | P7 / X3 | No | bridge | Short: two sentences + "v0 keeps rank order; edges-first is X3". Must say it is about positions in the prompt, not minima |
| 19 | Three citation contracts: inline tags, structured JSON, provider-native (Anthropic/Cohere) | K decisions; Claude arm; interview | **Missing** | C5 | No | core | Short: a 3-row table (what each guarantees; none checks support). Full: the Anthropic and Groq-JSON shapes |
| 20 | Book's way: highlighting **after** generation, a second call (Ch3 p.8–9/14); explanation ≠ attribution (Ch19 p.8/10) | G.1 | Yes (G.1) | C5 | No | core | Keep; move one line into Short |
| 21 | Page base: 0-based loader pages vs 1-based citations | label correctness | **Missing** | C1 | No | bridge | Short: one line + the repo example (cell 24 over `PyPDFLoader`) |
| 22 | Model tiers for generation: Groq default; Claude Haiku/Sonnet arms; the book's own tier advice (Ch3 p.10–11/14) | §9 experiment, K | **Missing** | C5 (Foundation §6.4) | No | core | Full only: tier table with cost per run |
| 23 | Temperature 0 is not determinism; replay is the guarantee | D.3 "repeatable runs" | **Incorrect** (overstated) | P1 / Foundation §2.7 | Exposed | bridge | Short: fix the sentence; Full: the Thinking Machines result |
| 24 | Caching and replay of every generation call | lab Task 9, LLMOps notebook | **Missing** (Task 9 calls Groq raw) | Foundation §2 | — | bridge | Full + LLMOps notebook: all calls via `llmops.cache` |
| 25 | Chunk text is data, not instructions (prompt injection) | D.2 blocks | P7 D.8 one line | D4 | No | next | Link only |
| 26 | Context assembly beyond v0: dedup, ordering, budgets, compression | J4, K | — | X1–X3 | No | next | Link only (ALCE: compression hurt citation quality) |

**Summary.** 9 gaps (5, 7, 9, 16, 17, 19, 21, 22, 24), 1 incorrect claim (23), and 4 bridges that exist only in P7, which Yash has not studied (1–3, 18). The core mechanism (10–15, 20) is taught well.

### 3. Quiz coverage

No `study/questions/C5_questions.md` or `study/reading/C5_*.md` exists. The lesson's Part L has 8 items (C5-R-01…03, C5-A-01…04, C5-T-01). There is no Short version yet, so the check is against what a Short lesson must contain:

| Existing item | Key point | Answerable from a Short lesson built from today's file? | Fix |
|---|---|---|---|
| C5-A-01 (MC-003 item) | sort by rank; no merging/overlap at query time | Only if idea 1 is in Short | Put the index/query diagram in Short |
| C5-A-03 | input budget 7,552 → 7,808 at toy W = 8,192 | **No**: the formula lives in P7 D.4 | Put the budget formula in Short (idea 3) |
| C5-A-04 | 802 → 1,442 tokens, ×1.80 | Yes if D.2's numbers stay in Short | — |
| C5-R-02 | names "citation precision" as the fix | **No**: never defined | Idea 16 definitions in Short |
| C5-R-03 | `max_tokens` covers reasoning | Yes (D.3), but wording must switch to `max_completion_tokens` | Idea 5 |
| Others | — | Yes | — |

Needed question titles for the new question file (R/A/T + interview):
- **R** (recall): C5-R-01 steps from records to a checked record · C5-R-02 what cited ⊆ retrieved checks and misses · C5-R-03 why assert on content · **C5-R-04** what `finish_reason="length"` means and why it has its own flag · **C5-R-05** three citation contracts and what each guarantees · **C5-R-06** why `reasoning_effort` and `max_completion_tokens` are always sent.
- **A** (application): C5-A-01 headers for ranks 3,1,4,2 (MC-003) · C5-A-02 invalid and unused ids · C5-A-03 output cap halves · C5-A-04 k doubles · **C5-A-05** parse a toy answer into citations and malformed tags · **C5-A-06** classify a failure using a context swap · **C5-A-07** does a k = 6 prompt fit a toy window with a 512 reserve? · **C5-A-08** cost of one 55-question run on Groq vs Haiku 5.5 from given token counts.
- **T** (transfer): C5-T-01 contracts assistant with clause ids · **C5-T-02** map retrieved chunks onto Anthropic custom-content documents: what replaces the subset check, what still needs checking?
- **Interview**: **C5-I-01** "How do you make a RAG system produce trustworthy citations?" (AIQ 04 Q28, MIT © 2026 Om; show the repo answer only after Yash's attempt).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| E-C5-1 | C5 lesson, Verification log ("none of the cited C5 cells has saved output except `reliable_rag.ipynb` cell 23") | `reliable_rag.ipynb` cell 18 also has a saved output (an uncited answer listing four agentic patterns) | Correct the sentence; the output is a useful exhibit (an answer from a permissive prompt with no citations) |
| E-C5-2 | C5 D.3 ("`temperature=0` for repeatable runs"); 06 §3.1 "temperature 0 [N] for repeatability" | Overstated: Groq seed is best effort, server batching varies even at T = 0 (Foundation §2.7) | "T = 0 reduces variation; only replay reproduces a run" |
| E-C5-3 | C5 D.3, K; lab Task 2 CHECK (`set(_kw) == {..., "max_tokens", ...}`); `c5_measure.py` L139–141; 06 §2.4/§3.1 | Groq deprecates `max_tokens` for `max_completion_tokens` (Foundation E3; confirmed in the API reference 2026-10-17). The lab CHECK will fail a learner who uses the new name | Switch in a recorded config change; update the CHECK to accept the new name and record which name was sent |
| E-C5-4 | `local_rag_huggingface_faiss.ipynb` cell 24 (repo; not ours to edit) and C5 G.2 | `[Page n]` uses `PyPDFLoader`'s 0-based `page` ([C5-7]); C5 G.2 does not mention the off-by-one | Add to C5 G.2 as an audit point; add a T1 "label page contains chunk text" test |
| E-C5-5 | Ext review §3a row 6 | The reasoning-token double-count CHECK was planned "before C6's first full v0 run" but is in neither the lab nor `c5_measure.py` | Add to the verify notebook (on recorded responses) and the apply-it tool |
| E-C5-6 | Lab Task 9 (cell `c5-35`) | Calls `Groq(...)` directly: no cache (violates D-32 "every external call cached"), SDK default `max_retries=2` (Foundation E8), and the empty-answer path loses the real `finish_reason` | Route through `llmops.cache` once it exists; until then, keep Task 9 off |
| E-C5-7 | 02 C5 card, Book line | Lists only Ch1 p.9/14 and Ch3 p.8–9/14 | Add Ch1 p.10/14, Ch3 p.6/14, Ch3 p.10–11/14 (model tiers, "I don't know"), Ch19 p.8/10 |
| E-C5-8 | 04 C5 row | Cites `local_rag…` cells 24, 28 but not 22 (prompt) or 26 (`ask`, the 02 card's cell); lists `helper_functions.py:L162-L205` and `crag.ipynb` cell 20 as citation sources (they are not; C5 G.2 already reports this) | Cells 22, 24, 26, 28; drop the helper lines |
| E-C5-9 | Book Appendix p.9/23 | A second place (besides p.5/23) that credits Ch19 with the citation trail; C5 G.1 lists only p.5 | Add p.9/23 to C5 G.1's inconsistency row |
| E-C5-10 | C5 lesson header ("P7 … C5 does not repeat that") | P7 is `not_started`, so C5 cannot assume it | Bridge ideas 1–3 and 18 in C5's Short (§2) |

### 5. What the research says

All external; opened 2026-10-17. Study and result first, then my interpretation ("For the project").

**[C5-1] Groq docs for `openai/gpt-oss-20b`** (Reasoning, Structured Outputs, API reference pages).
- **What the pages say.**
  - Reasoning page: `reasoning_effort` low / medium / high for GPT-OSS 20B. `reasoning_format` is **not supported** for gpt-oss. `include_reasoning` is supported; by default the reasoning text comes back in a `reasoning` field on the message; `include_reasoning=false` drops it. The two flags are mutually exclusive. `max_completion_tokens` default 1,024, which the page warns "may be too low for complex reasoning". It does **not** say whether reasoning tokens count against `max_completion_tokens`.
  - API reference: `max_tokens` is "Deprecated in favor of `max_completion_tokens`". For gpt-oss, "'medium' is the default value" of `reasoning_effort`; unsupported values return 400. `seed` is best effort only. `response_format` with `json_schema` is "preferred for models that support it"; `json_object` is the older JSON mode. The chat section lists **no `finish_reason` enum** (example shows "stop") and does **not** document `completion_tokens_details.reasoning_tokens` for chat (only the Responses endpoint documents `output_tokens_details.reasoning_tokens`).
  - Structured Outputs page: `openai/gpt-oss-20b` supports `json_schema` with **`strict: true`** (constrained decoding; "never producing invalid JSON"). Strict needs every property in `required` and `additionalProperties: false`. "Streaming and tool use are not currently supported with Structured Outputs." `json_object` mode guarantees syntax only.
- **Limits.** Docs, not measurements. The behaviour at the output cap, the real `finish_reason` values and whether `reasoning_tokens ≤ completion_tokens` remain **UNVERIFIED** until one logged call (ext review §3a row 6).
- **For the project.** (1) Send `max_completion_tokens` (Foundation E3); keep `max_tokens` only as the trace field name or record both. (2) Always send `reasoning_effort="low"` and `include_reasoning=false` **or** store the reasoning text: the reasoning field is model output and may name pages that the answer does not cite, so it must never be parsed for citations. (3) A JSON-citation arm is technically possible on Groq (`strict: true`), so the "inline tags vs JSON" comparison needs no new provider. (4) The groq 1.7.0 SDK type allows `stop`, `length`, `tool_calls`, `function_call` (C5_FACTS S-src); the docs do not list values, so `unexpected_finish_reason` stays.

**[C5-2] Anthropic, Citations** (https://platform.claude.com/docs/en/build-with-claude/citations; plus the `claude-api` skill, cached 2026-10-06).
- **What the page says.** GA on all platforms; "All active models support citations". Set `citations: {enabled: true}` on each `document` block (all or none). Three document types: plain text (chunked into sentences, cited by 0-indexed character range, exclusive end), PDF (sentences, 1-indexed page range, exclusive end; image-only scans are not citable), custom content (your blocks used as-is, cited by 0-indexed block range). `document_index` is 0-indexed across all documents in the request. The response splits into several `text` blocks, each cited block carrying `citations` with `cited_text`. `cited_text` does **not** count toward output tokens (nor toward input tokens when passed back). Enabling citations adds "a slight increase in input tokens". The page claims citations are "guaranteed to contain valid pointers to the provided documents" and that, in Anthropic's evaluations, the feature is "significantly more likely to cite the most relevant quotes" than prompt-based citing (no numbers given). **Citations + structured outputs (`output_config.format`) return a 400.** Works with prompt caching (cache the document blocks) and batch.
- **For RAG chunks** the page says: one plain-text document per chunk if you want sentence-level citations; custom content documents if you want no further chunking.
- **Limits.** Vendor documentation; the quality claim has no published numbers here. "Valid pointer" means **cited ⊆ provided by construction**; it says nothing about support (C5 D.7 still applies).
- **For the project.** A Claude arm can make the C5 subset check trivially true, which is a useful contrast: it moves the "cited but not retrieved" failure into the API contract and leaves only support to check. Map one retrieved chunk → one custom-content document (title = `climate:p10`, `context` = chunk id), and `document_index` + `content_block_location` resolve straight to `chunk_id`: finer than the v0 page label (fixes C5 J6). It is a **different citation contract**, so it is an experiment arm with its own parser, not a drop-in. Only the climate corpus may be sent.

**[C5-3] Interview repo `04-rag-and-retrieval/questions.md` Q28** (MIT, "Copyright (c) 2026 Om").
- **What it says.** Three layers: prompt/format (stable chunk ids, inline markers, an "I don't know" instruction that must be tested), verification ("mechanically validate that every cited ID exists in the provided set - free", then an entailment check per claim–citation pair), UX (deep links to the page or span). Measure citation precision and recall on a golden set.
- **For the project.** This is the interview frame for C5. Our v0 already does layer 1 and the free half of layer 2; layer 2's support check is V1/v5.0; layer 3 is the `[doc:page]` choice.

**[C5-4] ALCE: Gao, Yen, Yu, Chen, "Enabling Large Language Models to Generate Text with Citations", EMNLP 2023** (https://arxiv.org/abs/2305.14627; body read in the arXiv HTML, first ~100k of 128k characters).
- **The study.** A benchmark on three QA sets (ASQA and QAMPARI over 21M Wikipedia passages; ELI5 over the 899M-passage Sphere corpus). Retrieved passages are numbered and the model cites inline as `[1][2]`, at most 3 per statement; "Vanilla" gives the top 5 passages.
- **Metrics.** *Citation recall* (per statement, 0/1): the statement has at least one citation **and** the concatenated cited passages entail it, judged by the TRUE NLI model (T5-11B). *Citation precision* (per citation): a citation is "irrelevant" if it does not support the statement alone **and** removing it leaves the rest still supporting it.
- **Results.** ChatGPT, ASQA, Vanilla 5 passages: citation recall 73.6, precision 72.5, correctness (EM recall) 40.4. ELI5: citation recall 51.1. The abstract: the best models lack complete citation support about half the time on ELI5. Compressing passages (Summ/Snippet) helped correctness but **hurt** citation quality; for ChatGPT, citation quality plateaued at top-3 passages. Metric vs humans: κ 0.698 (recall), 0.525 (precision); accuracy 85.1% / 77.6%.
- **Limits (stated).** NLI cannot see partial support; ELI5 answers are open-ended; no multi-hop, maths or code. 2023 models (not gpt-oss).
- **For the project.** (1) ALCE's two metrics are exactly 06 §7.4's citation precision/recall, but ALCE judges them with an NLI model, which here means **a local model or a judge**, so they belong to V1/M3 and D-10, not to C5. (2) C5's deterministic checks are the **free necessary conditions** under ALCE's metrics: a citation that resolves to nothing has precision 0 for certain; a sentence with no citation has recall 0 for certain. Name this link in the lesson. (3) Numbered `[1]` citations (ALCE) vs `[doc:page]` (v0) is a design choice: block numbers are shorter but change with order, which v0 rejects (C5 D.4).

**[C5-5] Cohere, RAG with documents and citations** (https://docs.cohere.com/docs/retrieval-augmented-generation-rag, https://docs.cohere.com/docs/rag-citations).
- **What the pages say.** Chat v2 takes `documents` as strings or objects with `data` and an optional `id`; without `id`, ids are generated from list position. The response carries `citations`, each with `start`/`end` character offsets **in the answer**, the cited answer `text`, and `sources` (document `id` and content). `citation_options={"mode": ...}`: `accurate` is the default (citations added after the answer, "slightly higher latency"), `fast` cites inline during generation with slightly less precise relevance. Examples use `command-a-plus-05-2026` (a model id seen only in examples; availability for Yash's key **UNVERIFIED**). The page's "Accurate citations" example sets `"mode": "fast"` (a doc inconsistency).
- **Limits.** Docs only; no accuracy numbers.
- **For the project.** Cohere is the D-10 judge provider, not a generator, so a Cohere-citations arm would make the judge family equal the generator family (bias, `llm-as-judge`). Mention it in the lesson as a production pattern (span-level answer offsets, pass `id = chunk_id`), but **do not** plan a Cohere generation arm.

**[C5-6] Liu et al., "Lost in the Middle: How Language Models Use Long Contexts", TACL 2023** (https://arxiv.org/abs/2307.03172; abstract only). Multi-document QA and key-value retrieval; performance is often highest when the relevant information is at the beginning or end. **Bridge only:** P7 D.6 teaches it; C5 keeps rank order, and the J4 symptom (evidence at rank 3 of 4 unused) is where C5 links to it. Edges-first is an X3 experiment.

**[C5-7] langchain-community `PyPDFParser.lazy_parse`** (https://raw.githubusercontent.com/langchain-ai/langchain-community/main/libs/community/langchain_community/document_loaders/parsers/pdf.py, main branch, not the version the repo notebook pinned). Per page it sets `"page": page_number` from `enumerate(pdf_reader.pages)` (0-based) and `"page_label"` from the PDF's own labels. **For the project:** the repo's `[Page n]` headers (`local_rag_huggingface_faiss.ipynb` cell 24 over `PyPDFLoader`, cell 12) are one less than the page a reader opens. A `[doc:page]` citation is only as good as the page base; v0 uses 1-based PyMuPDF pages (06 §3.1). Add a T1 test: the label's page contains the chunk text.

**Current practice (2024–2026), from the sources above.**
- Three citation contracts coexist: (a) prompt-requested inline markers parsed by regex (ALCE, our v0, AIQ Q28); (b) structured output with a citations array (`reliable_rag.ipynb` cell 22's Pydantic model; Groq `json_schema` strict); (c) provider-native citations that tie spans to supplied documents (Anthropic `document` blocks, Cohere `documents`). (c) makes cited ⊆ provided true by construction; none of the three checks support.
- Anthropic's two native features conflict: citations + structured outputs = 400. A design wanting both must pick one.
- Reasoning models add a channel that is not the answer (Groq `reasoning` field). Citations must be parsed from `content` only.

**Pitfalls, with evidence.**

| Pitfall | Evidence |
|---|---|
| "Sources" printed = everything retrieved, not what was used | `local_rag_huggingface_faiss.ipynb` cell 28; C5 B.1 |
| Unknown citations dropped silently | `graph_rag_local_attribution.ipynb` cell 9; C5 B.2 |
| Empty or cut answer at the output cap; looks like a citation failure | O2 smoke call (empty at 12); C5 D.6 S5; Groq default 1,024 "may be too low" [C5-1] |
| Omitted `reasoning_effort` runs at `medium` | Groq API reference [C5-1] |
| Page labels off by one | [C5-7] + repo cell 24 |
| Valid label on a false claim | C5 T19; ALCE's NLI step exists for this [C5-4] |
| Compression helps correctness but hurts citation quality | ALCE Summ/Snippet [C5-4] (relevant to X2) |
| Citation format drift across providers (block numbers, `(doc:page)`) | C5 D.4 toys T07–T10 (hand-written, not measured) |

**How to evaluate C5 (retrieval and answer quality kept apart).**
- **Retrieval side (owned by C4/M2, read-only here):** was the gold page in the top-k (CE@4, Hit@4)? Needed to classify a citation failure (CR-11).
- **Answer side, deterministic (C5's own; tier 1):** `citation_subset_ok` rate, invalid-citation rate, malformed-tag rate, `no_citation` and `uncited_sentence` rates, exact abstention rate, `length_stop` rate, `empty` rate, citation page-hit (cited pages ∩ gold pages ≠ ∅; 06 §7.4).
- **Answer side, human (tier 2):** support per citation (precision) and per sentence (recall), labelled by hand on a sample, ALCE definitions. No judge before D-10.
- **Context swapping** (`rag-evaluation`): give the generator the gold chunk(s) in place of the retrieved set. Still wrong → generation; now right → retrieval. Cheap (one extra call per swapped item) and the cleanest C5 diagnostic.
- **Baseline:** v0 `answer_v1` itself. C5 has no earlier version; the first comparison is between arms at fixed retrieval (§9).

**Interview questions (3–5).**
1. "How do you make a RAG system produce trustworthy citations?" (AIQ 04 Q28, MIT © 2026 Om)
2. "You have retrieved chunks and a question. How do you actually build the prompt? Assume some documents are irrelevant and two of them contradict each other." (AIQ 03 Q30, MIT © 2026 Om)
3. "Your production code reads the response text but never checks `finish_reason` … Why is that a bug?" (AIQ 08 Q14, MIT © 2026 Om)
4. Our own: "An answer cites a page that was retrieved, but the claim is false. Which check catches it, and what does it cost?" (support check: NLI/judge/human; ALCE)
5. Our own: "Inline `[doc:page]` tags, JSON citations or a provider's citations API: what does each guarantee?"

### 6. Lesson blueprint

The existing lesson (Parts A–M) is strong on the mechanism. The rebuild keeps its numbers (C5_FACTS S1–S10) and reorders into the P3 shape: answer first → theory in one read → formula sheet → steps → verify → apply → check.

**The answer first (draft, 5 sentences).**
1. At query time, C5 takes C4's ranked chunks, writes them as numbered blocks labelled `(doc_id:page)`, fills a versioned template, and makes one model call; nothing is re-chunked or merged.
2. The model must cite every factual sentence as `[doc_id:page]`, or reply with one fixed sentence when the sources are not enough.
3. Code then parses the tags strictly, resolves each page to the retrieved chunk ids, and flags anything that points outside the retrieved set, is malformed, is missing, or was cut off by the output cap.
4. These checks are free and catch fake or broken citations, but they cannot tell whether a cited page really supports the sentence: that needs a human, an NLI model or a judge (V1, and the D-10 batch).
5. So C5's record keeps retrieval facts (what was supplied) apart from answer facts (what was cited, how the call ended), which is what lets C6 and M5 say which stage failed.

**The theory in one read (11 linked ideas, each with its formula or rule).**

| # | Idea | Formula / rule | Class |
|---|---|---|---|
| 1 | Two phases | index time: chunk(size, overlap) once; query time: arrange(top-k) per question. Overlap ∉ prompt | bridge (MC-003) |
| 2 | Prompt = rules + blocks + question | tokens(prompt) = rules (107) + Σ blocks + question + scaffolding; D-002 k = 4: **802** | bridge (P7) |
| 3 | Budget with a reserve | input budget = W − `max_completion_tokens` − margin; k fits if fixed + Σ blocks ≤ budget | bridge (P7 D.4) |
| 4 | One call, every parameter sent | `model` from `.env`, `temperature=0`, `max_completion_tokens`, `reasoning_effort="low"`; omitted effort ⇒ server `medium` | core |
| 5 | Output cap is shared | completion = reasoning + visible answer; check `reasoning_tokens ≤ completion_tokens`; `finish_reason="length"` ⇒ cut | core |
| 6 | Strict parse | valid ⇔ `re.fullmatch(r"\[[A-Za-z0-9_-]+:\d+\]")`; anything tag-like else ⇒ malformed | core |
| 7 | Resolve and subset | R = retrieved (doc, page) set; for each citation c: resolved(c) = {chunk ids on c's page}; ok ⇔ ∀c: resolved(c) ≠ ∅ ∧ no malformed | core |
| 8 | Missing and unused | `no_citation`: answer ∧ ¬abstained ∧ C = ∅; unused = retrieved ids − ∪ resolved | core |
| 9 | Abstention | abstained ⇔ normalise(text) = normalise(fixed sentence) | core |
| 10 | What code cannot see: support | ALCE citation recall (per sentence: cited passages entail it), precision (per citation: needed for support). Invalid ⇒ precision 0; uncited ⇒ recall 0 | bridge (V1) |
| 11 | Three citation contracts | inline tags (parse + subset check) · structured JSON (schema-valid, subset check still needed) · provider-native (cited ⊆ supplied by construction). None checks support | core |

Plus two short bridges placed where needed: lost in the middle (after idea 8, at the J4 symptom) and context swapping (after idea 10, as the way to classify a failure).

**Formula-sheet items.**
- `input_budget = W − max_completion_tokens − margin`
- `prompt_tokens(k) ≈ fixed + Σ_{i≤k} block_i` (D-002: 802 at k = 4; 1,442 at k = 8, ×1.80)
- `cost/query = in × p_in + completion × p_out` (Groq gpt-oss-20b: $0.075 / $0.30 per 1M; Foundation §6.2); reasoning is already inside `completion` if the check in idea 5 holds
- `citation_subset_ok = (invalid = ∅) ∧ (malformed = ∅)`
- `unused = k − |∪ resolved|` (k = 4, one cite: 3; k = 8: 7)
- ALCE: `recall_sent = 1[cited ≠ ∅ ∧ entails(cited, sentence)]`; `precision_cit = 1[recall = 1 ∧ ¬irrelevant(c)]`
- Abstention P / R / F1 and false-abstention rate (06 §7.4)

**Step-by-step outline (running example: Corpus D, the climate PDF; questions D-002 and D-009 from 06 §6.7, using the C5 lab's fixed MiniLM top-4 so no retrieval or API call is needed).**
1. D-002's four records arrive with ranks 1–4 on pages 24, 23, 10, 6; the gold sentence is in rank 3 (C5_FACTS S3).
2. Sort by rank, build four `[i] (climate:p)` blocks; count tokens: 107 + 695 = 802 (S4).
3. Budget check at a toy W = 8,192 with a 512 reserve: 7,552 available, so k = 4 fits easily (S8).
4. The call: show the exact keyword arguments; explain the server default and the reasoning field.
5. Toy answer T01 → parse → resolve to chunk 00027 → unused 00069, 00068, 00017 → no flags (S6).
6. Toy answers T02 (cites p.12), T07–T10 (malformed), T05 (no tag), the cut-off reply (S5): one flag each.
7. D-009 (unanswerable): T18 abstains (all unused, correct); T19 cites p.29 with a fact not in the PDF and passes every check (S6): the limit.
8. Classify T19 and J4 with a context swap: feed the gold context (or none exists) and re-ask (the swap answer is a recorded call, labelled as one run).
9. Compare contracts on the same D-002 context: inline tags vs a JSON answer vs Anthropic custom-content documents (shapes only in Short; recorded runs in the LLMOps notebook).

**Visuals that earn their place.**

| Visual | The one thing it shows |
|---|---|
| Two-row pipeline (index row / query row), C5 highlighted on the query row | Overlap lives in the other row (MC-003) |
| Stacked bar of the 802 prompt tokens (rules, 4 blocks, question) + a k = 1…8 line (Plotly in the notebook) | The chunks are the budget; k = 8 is ×1.80, not ×2 |
| Output-cap bar: reasoning + answer inside `max_completion_tokens`, with a "length" cut | Why an answer can be empty or cut with HTTP 200 |
| Venn of retrieved pages vs cited pages (D-009: {29, 10, 24} vs {29, 1}) | Invalid = cited outside; unused = retrieved never cited |
| Flag decision tree (empty → length → abstained → malformed → invalid → no citation → uncited sentence) | Which flag fires first, and that "subset ok" can coexist with a false claim |
| 3-column contract table (inline / JSON / native) with ✓/✗ for "pointer valid", "format valid", "support" | Only support is never guaranteed |

**Full-only details.** ALCE's NLI judge and its κ; Anthropic citation response shapes (indices, `cited_text` not billed as output); Groq `json_schema` strict rules; Cohere's accurate vs fast citation modes; the Thinking Machines non-determinism result; the 0-based loader page trap with the repo cell; the repo audit table (C5 G.2); the Appendix p.5/p.9 inconsistency; model-tier table and costs; why repair loops are not in v0.

### 7. Verify notebook plan

`study/notebooks/C5_generation_verify.ipynb`. Framework-free. Imports the reference functions from `sources/verification/C5/c5_measure.py` (read-only) so every number matches C5_FACTS.

| Section | Recomputes | Data / code | Check against |
|---|---|---|---|
| 1. Snapshot and fixture | 33 pages, `snapshot_id ea07572562ac`, 97 chunks, D-002/D-009 top-4 | climate PDF + `c5_measure` S1–S3 (MiniLM, local) | C5_FACTS S1–S3 |
| 2. Prompt tokens | 107 / 695 / 802; blocks 199, 133, 196, 152; k = 8 → 1,442; 10 seeds 771–894 | `build_messages` + tiktoken `o200k_harmony` | S4 |
| 3. Budget | input budget at toy W = 8,192 for reserves 256 / 512 / 1,024 (7,808 / 7,552 / 7,040); largest k that fits | formula + block sizes | S8 + new derived row |
| 4. Flags on toy answers | all 19 toys + the cut-off reply; flag table | `make_answer` | S5, S6 |
| 5. ALCE link (new) | for each toy: "precision certainly 0?" (invalid citation), "recall certainly 0?" (uncited sentence), "needs support label" (everything else) | toy table | hand-derived key in the notebook |
| 6. Contract shapes (new) | parse a stored **example** Groq JSON answer and a stored **example** Anthropic citations response (both hand-written toys shaped like the docs, labelled toy) into the same record | `pydantic`, `jsonschema` | equal `citations` lists |
| 7. Recorded calls (optional, replay) | if a replay pack exists: per-seed flags, `finish_reason`, `reasoning_tokens ≤ completion_tokens`, cost/query, one context-swap pair | `llmops.cache` in `replay` mode | prints "no pack: skipped" otherwise |

- **Charts (Plotly):** stacked token bar + k-sweep line; output-cap bar; flag counts over the toys; retrieved-vs-cited page sets for D-009.
- **LLM/API calls:** none new. Section 7 reads the cache only (`LLMOPS_CACHE_MODE=replay`), so it runs with no key and no credits.
- **Offline:** yes (MiniLM from the local HF cache). **Runtime:** about 30–60 s (MiniLM load dominates; C5_FACTS S3 run).

### 8. Apply-it tool plan and real-world checklist

`study/tools/citation_check.py` (pattern of `bm25_fit_check.py`): a **citation-sanity check on Yash's own question + answer traces**.

- **Input.** A JSONL file, one object per answer: `question`, `retrieved` (list of `rank, chunk_id, doc_id, page, text`), `answer_text`, optional `finish_reason`, `usage` (`prompt_tokens`, `completion_tokens`, `reasoning_tokens`), optional `messages` (to count prompt tokens), optional `context_window`, `max_completion_tokens`. Accepts C5/C6 records directly (06 §2.5 names). Options: `--tag-pattern` (default `[doc_id:page]`; e.g. clause ids, C5-T-01), `--abstain "<sentence>"`, `--prices prices.json`.
- **Output.** A per-answer table (flags, resolved ids, invalid, malformed, unused, uncited sentences), a summary (rates with `n`), a "read these first" list, and a recommendation block. Writes `citation_check_<date>.md` + `.json` next to the input. No API call, ever; works on recorded traces.

**Real-world checklist (12).**

| # | Check | Auto / manual | How |
|---|---|---|---|
| 1 | Every citation tag matches the strict grammar | auto | regex; malformed list and rate |
| 2 | Cited ⊆ retrieved (each citation resolves to ≥ 1 retrieved chunk) | auto | page → chunk resolution; invalid rate |
| 3 | No factual sentence without a citation | auto (heuristic) | sentence splitter; `uncited_sentence` count; tool prints the splitter's limits |
| 4 | Answers with no citation at all | auto | `no_citation` rate |
| 5 | Abstention is the exact sentence, not a paraphrase | auto + manual | exact match after normalising; tool lists refusal-like paraphrases ("cannot", "not enough") for Yash to read |
| 6 | The call ended normally | auto | `finish_reason`: `length_stop`, `unexpected_finish_reason`, `empty` |
| 7 | Reasoning tokens are inside completion tokens | auto | `reasoning_tokens ≤ completion_tokens` where present; else "unknown" |
| 8 | Prompt fits the window with the output reserve | auto | tokens(messages) + `max_completion_tokens` + margin ≤ W (tiktoken `o200k_harmony` for gpt-oss; for other models, provider counts or "unknown") |
| 9 | Cost per answer and per run | auto | `prices.json` × usage; "cost if called" |
| 10 | Page labels point at the right page | auto (if text present) | the cited chunk's text appears on that page of the source (catches 0-based labels) |
| 11 | Each cited page supports its sentence | manual | the tool prints sentence + cited chunk text side by side for a sample of 10; Yash labels supported / partly / not (ALCE definitions); labels saved to JSONL |
| 12 | Unused evidence: the gold-looking chunk was retrieved but not cited and the answer is wrong | manual | the tool lists answers with unused chunks that share rare terms with the question; Yash reads them (J4; lost in the middle) |

**Recommendation logic.**
- Malformed > 5% → the prompt's citation rule is not followed: try a versioned `answer_v2` with one example, or a JSON contract (do not repair in code).
- Any invalid citation → generation problem: log rate; consider a provider-native contract arm; never drop silently.
- `length_stop` or `empty` > 0 → raise `max_completion_tokens` or lower `reasoning_effort`, as a recorded config change.
- Check 7 fails → cost must use completion only; flag the cost formula.
- Check 8 fails → reduce k or chunk size (X3); never truncate silently.
- Check 10 fails → fix page numbering at parsing (C1) before anything else.
- Abstention paraphrases > 0 → measure; the fixed sentence is the contract.
- Many uncited sentences with `subset_ok` true → the support check (V1) is the next step; the subset check is passing for the wrong reason.

### 9. LLMOps notebook plan

`study/notebooks/C5_generation_llmops.ipynb`. Follows Foundation §12 row "2 · C5–C6": Groq generation through `CachedChatModel`; a plain function **or** a small LCEL chain; full v0 trace; deterministic answer checks + human labels; cost/query and p95; prompt version `answer_v1`; first golden run feeds the monitor page.

**Framework build (pieces mapped to the mechanism).**

| Mechanism step (lesson) | Framework piece | Default the lesson warns about |
|---|---|---|
| C4 records (fixed) | a `RunnableLambda` that loads the cached C4 top-4 (no retriever call) | `VectorStoreRetriever` k = 4 default; not used |
| `build_context` (rank sort, headers) | `RunnableLambda(build_context)` (the lesson's function, unchanged) | `RunnableParallel(answer=…, sources=retriever)` = "sources" ≠ citations (repo cell 28): shown as an anti-pattern cell |
| Template file | `ChatPromptTemplate.from_messages` built from `prompts/answer_v1.txt` (split rule IA-2); sha256 recorded | Hub prompts not used (Foundation §7) |
| `call_llm` | `CachedChatModel(provider="groq", model=$GROQ_MODEL_ID, params={temperature: 0, max_completion_tokens: 512, reasoning_effort: "low", include_reasoning: <decision>})` | `ChatGroq`: `temperature=0.7`, `max_retries=2`, `reasoning_effort=None` → server `medium` (Foundation §9.2); `langchain-groq` conflicts with groq 1.7.0, so it is shown read-only |
| `parse_citations` + `check_citations` + `make_answer` | `RunnableLambda` parser returning the C5 record | `StrOutputParser` would return text only; reasoning must not be parsed |
| JSON arm | `CachedChatModel` with `response_format={"type":"json_schema", strict: true}` and a Pydantic schema `{sentences:[{text, citations:[str]}], abstained: bool}`, then the **same** subset check | strict needs all fields required + `additionalProperties: false` [C5-1] |
| Claude arm (optional) | `CachedChatModel(provider="anthropic", model="claude-haiku-5-5", params={output_config.effort: "low", max_tokens: …})`; second variant with `document` blocks (custom content, one block per chunk, `citations.enabled`) | no `temperature` (400); thinking tokens count as output; citations + `output_config.format` = 400 [C5-2] |

Chain: `load_top4 | build_context | prompt | model | parse_and_check`. It is linear, so **no LangGraph** (Foundation §9.1). A plain-function version sits beside it, and a cell asserts both give identical records on replay.

**External calls (all through `llmops.cache`; recorded once, then replay).**

| Call set | Provider / model | Calls |
|---|---|---|
| A0 v0 inline tags, 10 draft seeds | Groq `openai/gpt-oss-20b` | 10 |
| A1 JSON citations (strict schema), same seeds | Groq | 10 |
| Context swap: gold chunk(s) only, answerable seeds (8) | Groq | 8 |
| Variance sample 1 of A0 (`record`, sample = 1) | Groq | 10 |
| Golden dev run once M1 exists (55 items × A0, A1) | Groq | 110 |
| Optional Claude: Haiku 5.5 inline + Haiku 5.5 Citations API, 10 seeds | Anthropic | 20 |
| Optional Claude: Sonnet 5.5 inline, 10 seeds | Anthropic | 10 |

Replay: with the pack present the whole notebook runs with `LLMOPS_CACHE_MODE=replay`, no key, no network. A missing key raises `ReplayMiss` with the record command.

**Cost and time per run** (my estimate, not measured: input ≈ 920 tokens/question = local 771–894 + ~71 template overhead (P1 B.3); output at the cap; prices Foundation §6.2).

| Model | 10 questions (cap 512 / 1,024) | 55 questions (cap 512 / 1,024) |
|---|---|---|
| Groq gpt-oss-20b | $0.0022 / $0.0038 | $0.012 / $0.021 |
| Claude Haiku 5.5 | $0.0035 / $0.0060 | $0.019 / $0.033 |
| Claude Sonnet 5.5 | $0.070 / $0.12 | $0.38 / $0.66 |

Claude rows are lower bounds (thinking counts as output, so its cap must be larger; the Citations API adds "slight" input overhead, size **UNVERIFIED**). Time, not money, binds on Groq: 55 × ~1,950 tokens ≈ 107K tokens ⇒ ≥ 13.4 min at 8K TPM and about half of the 200K daily quota (plan **UNVERIFIED**, Foundation §6.3).

**Tracing.** Default JSONL (06 §2.5 + Foundation §3.3 spans): root (`run_id`, `config_hash`, `prompt_version`, `template_sha256`, `cache_mode`); context span (chunk ids, `context_tokens`); LLM span (model requested/returned, `system_fingerprint`, every sent parameter, tokens incl. reasoning and cached, `finish_reason`, latency, `queue_time`, cost, `cache_hit`, `cache_key`, `http_attempts`); evaluator span (all C5 flags as attributes). Local viewer: Phoenix (`uvx`), `openinference-instrumentation-langchain`. LangSmith: only after `privacy.assert_corpus_is("D")`, inside `tracing_context(enabled=True)`; chunk text allowed for Corpus D only.

**Dataset and evaluators.** Dataset: the 10 draft seeds now (06 §6.7, 8 answerable + 2 unanswerable), then M1's dev split; LangSmith mirror only for Corpus D. Evaluators, tier 1 (Foundation §5), wrapped as `(inputs, outputs, reference_outputs) → {key, score}`: `citation_subset_ok`, `invalid_rate`, `malformed_rate`, `no_citation`, `uncited_sentences`, `abstained_correctly` (vs `answerable`), `length_stop`, `empty`, `reasoning_le_completion`, `citation_page_hit` (vs gold pages), `json_schema_valid` (A1). Tier 2: Yash labels support for ~10 answers per arm (ALCE recall/precision definitions), stored as JSONL; Codex labels a copy for calibration (D-10). No judge.

**Experiment.** There is no earlier version of the answer step; the "previous version" is v0's own contract. Pre-register (06 §9.1): **A0 (inline tags) vs A1 (strict JSON)** at fixed retrieval (cached C4 top-4), one variable (the citation contract). Primary: invalid + malformed rate; guards: abstention F1 on the 2 unanswerable seeds, page-hit, tokens/question, p95 latency. Optional Claude arms are separate experiments (model change ≠ contract change; Foundation §6.4). With n = 10, report counts, not significance; rerun on the dev split later.

**Cost / latency / tokens.** Per arm: cost/query (cost if called, cost paid), p50/p95 latency excluding cache hits, input / completion / reasoning tokens, reasoning share (reasoning / completion), `length_stop` rate.

**Prompt and config versioning.** `prompts/answer_v1.txt` (never edited), `prompts/answer_v1_json.txt` for A1, `prompts/answer_v1_claude_docs.txt` for the native arm; schema file `prompts/answer_v1_json.schema.json` hashed into the config. The parameter rename (`max_tokens` → `max_completion_tokens`) is its own recorded config change with a replay-miss expected (new cache key).

**Monitoring and feedback.** Monitor page rows (Foundation §8.3): `length_stop` > 5%; invalid or malformed rate up vs the champion; abstention rate shift; reasoning share up (silent effort drift); new `system_fingerprint`; replay misses. A failing trace goes to the M5 error-analysis log with its flags; confirmed new failure modes become golden items and a T1 test on recorded responses (e.g. "this answer must flag `cited_not_retrieved`").

**Place in the lifecycle.** Analyze: read every A0 answer, open-code citation failures (`error-analysis`). Measure: tier-1 evaluators + human support labels (`code-based-evaluators`, `rag-evaluation`). Improve: contract arm, effort or cap changes (`improving-llm-agents`). dev → CI → monitor: replay test in CI, monitor page (`ci-cd-evals`, `llm-observability`). Skills used: `evals-foundations`, `rag-evaluation` (context swapping), `code-based-evaluators`, `llm-observability`, `ci-cd-evals`, `error-analysis`.

### 10. Tools, frameworks, libraries and LLMs

Pins reuse Foundation §11 (PyPI JSON API, 2026-10-17, newest release ≥ 2 weeks old). "Installed" from `uv pip list` (read-only) today. C5 needs **no library beyond the Foundation set**.

| Purpose | Library / model / service | Version | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Generation (default) | Groq `openai/gpt-oss-20b` via `groq` SDK | groq 1.7.0 (keep); model id from `.env` | yes | no (API); yes in replay | $0.075 / $0.30 per 1M; ≈ $0.002–0.004 per 10 questions; ≈ $0.012–0.021 per 55 | Apache-2.0 (SDK) | yes (D-04) |
| LLM feature: `reasoning_effort` low/medium/high | Groq | — | — | — | default `medium` if omitted | — | yes (verified docs) |
| LLM feature: `max_completion_tokens` (replaces `max_tokens`) | Groq | — | — | — | default 1,024 | — | yes (verified docs); course switch pending (E-C5-3) |
| LLM feature: `include_reasoning` / `reasoning` field (`reasoning_format` not supported on gpt-oss) | Groq | — | — | — | none | — | yes (verified docs) |
| LLM feature: structured outputs `json_schema` strict | Groq gpt-oss-20b | — | — | — | none extra | — | yes (verified docs; no streaming/tools with it) |
| LLM feature: `finish_reason` values | Groq | — | — | — | — | — | docs list none; SDK type: stop/length/tool_calls/function_call (C5_FACTS) |
| Claude comparison arm (quality-decides tier) | `claude-sonnet-5-5` via `anthropic` | anthropic 1.11.0 | no | no | $2 / $10 per 1M; ≈ $0.07–0.12 per 10 q; ≈ $0.38–0.66 per 55 (lower bound) | MIT | yes, when credits (D-32); comparison arm only (Foundation §6.4) |
| Claude cheap arm + Citations API | `claude-haiku-5-5` | anthropic 1.11.0 | no | no | $0.10 / $0.50 per 1M; ≈ $0.004–0.006 per 10 q | MIT | yes, when credits |
| LLM feature: Claude Citations (`document` blocks, custom content) | Anthropic | — | — | — | `cited_text` not billed as output; slight input overhead (size **UNVERIFIED**) | — | yes; incompatible with `output_config.format` |
| Cohere chat citations | Cohere Command family | cohere 7.2.0 | yes | no | — | MIT | **not used** for generation (Cohere is the D-10 judge family) |
| Local token counts | `tiktoken` (`o200k_harmony`) | 0.14.0 | yes | yes | — | MIT | yes |
| JSON schema for the JSON arm and records | `pydantic` / `jsonschema` | 2.13.5 / 4.26.0 | yes | yes | — | MIT | yes |
| Charts | `plotly` | 7.1.0 | yes | yes | — | MIT | yes |
| Framework core (LCEL chain, adapters) | `langchain-core` | 1.6.6 | no | yes | — | MIT | yes (D-32, after mechanism) |
| Graphs | `langgraph` | 1.2.12 | no | yes | — | MIT | **not needed for C5** (linear chain) |
| Groq via LangChain | `langchain-groq` | 1.1.3 | no | — | — | MIT | **conflict** (needs groq < 1.0): read-only cell only |
| Claude via LangChain (optional) | `langchain-anthropic` | 1.7.5 | no | no | as anthropic | MIT | optional; adapter preferred |
| Cohere via LangChain | `langchain-cohere` | 0.6.0 | no | — | — | MIT | **conflict** (needs cohere < 6); not needed |
| Community loaders (repo reading only) | `langchain-community` | — | no | — | — | MIT | not needed |
| Hosted tracing / datasets | `langsmith` | 0.14.4 | no | SDK yes | free plan; `LANGSMITH_API_KEY` | MIT | yes, Corpus D only |
| Local tracing | JSONL (default) + `arize-phoenix-otel` 0.17.2 + `openinference-instrumentation-langchain` 0.1.78 / `-groq` 0.1.31 / `-anthropic` 3.0.1; viewer `uvx arize-phoenix@20.19.0 serve` | as listed | no | yes | — | Apache-2.0; server ELv2 | yes; groq-1.7 instrumentor support **UNVERIFIED** |
| Cache / replay / cost / evals | `study/llmops/` (Foundation §10, plan) | — | not built | yes | — | ours | yes (required) |

Install lines (**not run**; same as Foundation):
```text
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4
uv add --group llmops arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78 openinference-instrumentation-groq==0.1.31
uv add --group llmops anthropic==1.11.0 openinference-instrumentation-anthropic==3.0.1     # only when Claude credits exist
uvx arize-phoenix@20.19.0 serve                                                              # on demand; not a project dependency
```

Keys: present `GROQ_API_KEY`, `GROQ_MODEL_ID` (and `COHERE_API_KEY`, not used by C5's generation). Add when needed: `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY` (+ `LANGSMITH_ENDPOINT`). Never put `LANGSMITH_TRACING` in `.env`. Weight: nothing heavy; no GPU.

### 11. Open questions for Yash (preferences only)

1. Should the trace keep Groq's reasoning text (`include_reasoning=true`, stored but never parsed), or drop it (`false`) to keep traces small? Either works; storing it helps you read why an answer went wrong.
2. When you have Claude credits, which comparison arm do you want first: **Haiku 5.5** (cheap, can also try the Citations API) or **Sonnet 5.5** (about 20× the cost, the "best answer" tier)?

---

## Concept C6: Baseline pipeline v0 end-to-end + provenance trace

### 1. Sources checked

**Book pages (opened 2026-10-17, PyMuPDF text of each page):**

| Cite | What is on the page (paraphrase) | 02/04 claim | Verdict |
|---|---|---|---|
| Ch1 p.1/14 | The problem: a model answers from memory and may hallucinate | — | ok (motivation) |
| Ch1 p.2/14 | RAG = search your documents before answering; closed-book vs open-book exam | — | ok |
| Ch1 p.3/14 | No retraining; store, retrieve, hand pieces as context. "How It Works": two phases, offline (once per document) and online (per question) | 02: p.3–10 = full pipeline | **ok** (pipeline starts at the foot of p.3) |
| Ch1 p.4/14 | Step 1 load page by page (poor extraction → poor retrieval); Step 2 chunks of about 1,000 chars, 200 overlap | — | ok |
| Ch1 p.5/14 | Step 3 clean (after splitting); Step 4 embeddings | — | ok |
| Ch1 p.6/14 | Embeddings as meaning coordinates; Step 5 vector database (FAISS) | — | ok |
| Ch1 p.7/14 | Preparation sketch, 5 steps (step 3 cleans each chunk) | 04: p.7 sketch | ok |
| Ch1 p.8/14 | Step 6 embed the query by the exact same process; Step 7 top 2–5 nearest chunks | — | ok |
| Ch1 p.9/14 | Step 8 generate the grounded answer; two-row figure introduced | — | ok |
| Ch1 p.10/14 | Query sketch, 6 steps; "The Role of Chunk Size" starts | 04: p.10 sketch | ok |
| Ch1 p.11/14 | Too large / just right; "Where Simple RAG Falls Short" starts at the foot of the page | 02: p.11–12 = falls short | **ok** |
| Ch1 p.12/14 | Scattered-evidence and multi-concept questions; limits are design boundaries, not bugs; when to use / overkill | — | ok |
| Ch1 p.13/14 | Trade-offs table (one embedding call + one search + one LLM call); claim that answer quality depends entirely on retrieval | not in 02's C6 card | **missing from 02** (C6 lesson already uses it, G.1) |
| Ch1 p.14/14 | Closing: simple RAG's limits motivate the rest of the book | — | ok |
| App p.4–5/23 | Six symptom families (wrong documents, missing info, wrong order, wrong/made-up answer, content type, cannot measure) | — | ok (M5 link) |
| App p.6/23 | Layer 1: get the basic pipeline working end to end; do not optimise early | 02: App p.6–7 | **ok** |
| App p.7/23 | Layers 3–5; Layer 5 = measurement; the common mistake is jumping to verification before retrieval works | 02: App p.6–7 | **ok**. Note: the book puts measurement in Layer 5 (last); the course measures right after v0 (02 principle 2) |
| App p.12/23 | Key takeaways: diagnose which stage underperforms; measure before and after every change | not in 02's C6 card | useful for D.5 (stage diagnosis) |
| Ch22 p.8/19 | Faithfulness isolates generation; low faithfulness + high context relevance → model or prompt | C6 lesson G.1 | ok |
| Ch22 p.13/19 | Component-level vs end-to-end evaluation; component metrics tell you where to look when an end-to-end score drops | C6 lesson G.1 | ok |
| Ch22 p.14–15/19 | Latency: time to first token, total, per component; percentiles not averages; cost per query; more K = more cost | C6 lesson G.1 cites p.14 only | ok; p.15/19 (cost side, production monitoring loop) is also relevant to the LLMOps notebook |


**Repo notebooks and cells** (`upstream/RAG_Techniques` @ `009adba`, 0-based; JSON read 2026-10-17):

| Cite | What the cell does | 02/04 claim | Verdict |
|---|---|---|---|
| `simple_rag.ipynb` cell 10 | `encode_pdf`: PyPDFLoader → recursive 1000/200 chars (`length_function=len`) → tab cleaner after split → OpenAI embeddings → `FAISS.from_documents` | — | ok |
| `simple_rag.ipynb` cells 13, 15, 17 | k = 2 retriever; prints texts only (`helper_functions.py` L147 keeps `page_content`, drops page and score); cell 17 runs `evaluate_rag` (OpenAI only) | 02: no generation step | **ok** (DV-01 confirmed) |
| `simple_rag_with_llamaindex.ipynb` cells 4, 9, 11, 13, 14, 16, 23 | 200/50 **tokens** (cell 4); `FaissVectorStore` built (cell 9); cleaner replaces tabs **and** space + newline (cell 11); cell 13 = `SentenceSplitter` + `IngestionPipeline(transformations=[TextCleaner(), splitter], vector_store=vector_store)`; cell 14 `pipeline.run`; cell 16 `VectorStoreIndex(nodes)`, top_k 2; cell 23 `as_query_engine` (generation by the global default LLM) | 02: "FAISS store likely bypassed" | **Confirmed by reading** (see §4 E-3 and §5 [C6-5]): the pipeline has no embedding step, so no node carries an embedding and nothing reaches FAISS; cell 16 then builds a fresh default in-memory index. Not run (llama-index not installed, OpenAI key absent) |
| `local_rag_huggingface_faiss.ipynb` cells 0, 10–30 | bge-base local embeddings, 1000/200 chars, `TOP_K = 3` (cell 10); PyPDFLoader (cell 12); FAISS (16); remote `HuggingFaceEndpoint` zephyr-7b (20); context-only prompt with a refusal sentence (22); LCEL chain `{"context": retriever \| format_docs, "question": RunnablePassthrough()} \| prompt \| llm \| StrOutputParser()` with `[Page n]` labels (24); `split("Answer:")[-1]` post-processing (26); `RunnableParallel(answer=rag_chain, sources=retriever)` (28); `evaluate_rag(rag_chain, retriever)` (30) | 02: "closest full pipeline" | ok, with **two new findings** (§4 E-4, E-5): cell 28 runs the retriever **twice** per query, and cell 24's `[Page n]` labels use PyPDFLoader's `page` metadata, which is 0-based ([C6-6], verified on current `main`; the notebook pins no langchain version). No saved outputs anywhere in the notebook |

**Interview repo** (`upstream/AI-Engineer-Interview-Questions`, MIT, "Copyright (c) 2026 Om"; quotes allowed with this notice):
- `04-rag-and-retrieval/questions.md` Q3 "Walk me through every stage of a production RAG pipeline, from raw documents to a cited answer." Its answer contains the compounding example (90% × 90% × 90% ≈ 73%) = the external review's AIQ 04 Q3 item.
- `07-evaluation-and-observability/questions.md` Q8 (what to log per LLM call), Q13 (OTel GenAI conventions: still Development stability), Q22 (evaluate RAG by component and end to end), Q42 (observability stack, what a good trace looks like), Q50 (deterministic replay harness; Foundation §2.7 already uses it).
- `12-coding-challenges/08_semantic_search_rag.py` (retrieval core + numbered citations + recall@k, with a stable-hash note) and `11_rate_limiter_and_retry.py` (token bucket charged with estimated prompt + max output tokens: exactly the Groq 8K TPM planner).

**AI Eval book:** AE Ch3, 'Open Coding: Reading and Labeling Traces' and 'Axial Coding: Structuring Failure Modes' (read; paraphrased in §5).

**Project skills read:** `rag-evaluation`, `llm-observability`, `evals-foundations`, `error-analysis`, `ci-cd-evals`, `code-based-evaluators`.

**External sources:** [C6-1] Lewis et al. 2020 (verified) · [C6-2] Barnett et al. 2024 (verified) · [C6-3] OpenInference semantic conventions (verified) · [C6-4] langchain-core `passthrough.py` (verified) · [C6-5] llama-index-core `ingestion/pipeline.py` (verified on main) · [C6-6] langchain-community `PyPDFParser` (verified on main) · [C6-7] Husain 2025 field guide (verified) · [C6-8] Gao et al. survey (abstract only). URLs in Notes (f).

**Existing course files audited:** `concepts/C6_v0_pipeline.md` (Parts A–M, 632 lines; D.5 ladder; H.1 Task 10 already carries the open-coding columns from external review §3a row 7; M.4 already says "first open codes"), `labs/C6_v0_pipeline.ipynb` (12 tasks; S11 lab test 12/12), `sources/verification/C6/C6_FACTS.md` (S1–S11, S-src 122 PASS), `c6_reference_v0.py`, `example_trace_D-002.json`, `example_index_manifest.json`, `toy_traces.json`. No `study/reading/C6_*.md` and no `study/questions/C6_questions.md` exist. Tracker: C6 `not_started`.

### 2. Gap audit

Tracker (2026-10-17): every Phase 1–2 concept is `not_started` except P1 (`exposed`). C6 is an integration concept, so most of its ideas are **bridges** from C1–C5, P1, P6 and P7, none of which Yash has studied. "Written" (the lessons exist) is not "studied".

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | Two phases: index time (once per corpus × config) vs query time (once per question) | Book Ch1 p.3/14; C6 D.1; Task 1 | Yes, C6 D.1 | C6 (book Ch1) | no | core | Keep. Add the call count per phase (index: ⌈chunks/96⌉ embed calls; query: 1 embed + 1 LLM), which the LLMOps part needs |
| 2 | The artifact chain and its join keys (page → offsets → `chunk_id` → vector row → score → context → citation) | D.2–D.4; Gate 2→3 item 2 | Yes, D.2–D.4 | C6 | no | core | Keep; make it the Short spine with one diagram |
| 3 | The names: `snapshot_id`, `params_hash`, `embed_hash`, `config_hash`, `index_manifest_hash`, `prompt.sha256` | D.2 table, flashcards | Yes, but as one dense 7-row table | C1, C2, C3 | no | bridge | Short: three names only (`snapshot_id` = the text, `params_hash` = the chunking, `embed_hash` = the embedder); the rest in Full |
| 4 | The trace record (06 §2.5) | D.3, Task 7 | **Incomplete**: D.3 and the lab omit `llm.max_tokens`, `reasoning_effort`, `finish_reason` (06 §2.5 [N] since 2026-10-09) and the Foundation E4 fields | C6 | no | core | Update the field table; one schema file (JSON Schema) that the lab, tool and LLMOps notebook all validate against (§4 E-6) |
| 5 | Trace as a **tree of spans** (chain → embedding → retriever → prompt → LLM), OpenInference kinds | Interview (AIQ 07 Q42); LLMOps notebook | **Missing** | C6 (D1 deepens it) | no | core (Full) | Full: the same record drawn as spans, with the field → attribute map ([C6-3]) |
| 6 | Provenance round trip: citation `[doc:page]` → resolved chunks ⊆ context → page segment → `doc_text[a:b]` | D.4 step 5; Part F step 2 | Partly (D.4 shows it once) | C5 + C6 | no | core | Name it "the round trip" and give it as a 4-step check; the apply-it tool automates it |
| 7 | Which stage failed: the first broken artifact, upstream to downstream (the ladder) | D.5, Task 9, J | Yes, D.5 | C6 | no | core | Keep; add the Barnett FP mapping in Full ([C6-2]) |
| 8 | Retrieval vs generation; the "danger zone" (correct answer, evidence never retrieved) | D.5 TOY-7, J4 | Yes | C6 / 06 §7.1 | no | core | Keep |
| 9 | Gold spans, CE@4 and Hit@4 | D.4 step 3 ("CE@4 = 1"), FACTS S5 | **Missing in C6**: used, never defined | P6, M1, M2 | no | bridge | Two sentences in Short: a gold span is the character range that proves the answer; CE@4 = 1 when every needed fact lies wholly inside the top-4 chunks |
| 10 | Compounding stage errors (0.9³ = 0.729) and why independence is an assumption | External review §4 C6 item; AIQ 04 Q3 | **Missing** | C6 | no | core | Short: one paragraph + a small slider chart; state both assumptions and the TOY-7 counterexample |
| 11 | Reproducible retrieval vs non-repeatable generation; replay as the only guarantee | D.6 | **Incomplete**: D.6 still says "UNVERIFIED for Groq" and names the old cache key | Foundation §2 (O2/D2) | no | bridge | Short: "retrieval repeats byte for byte; answers repeat only from the cache". Full: record / replay / auto, cache key fields |
| 12 | `finish_reason`, reasoning tokens, the output cap (`max_completion_tokens`) | Part A6; Task 10 flags | Partly (A6, lab printer) | P1, C5 | P1 exposed | bridge | Short: one line on why an empty or cut answer is a failure, not a skip |
| 13 | Fixed abstention string and its exact-match detection | Ladder check 5; Task 10 | In C5 | P7, C5 | no | bridge | One line where check 5 appears |
| 14 | Latency per stage (p50/p95, method named) and cost per query (cost if called vs cost paid) | Gate 3→4 last item; trace `latency_ms`, `cost_usd_estimate` | **Missing**: the fields exist, nothing teaches how to read them | C6 (D2 deepens) | no | core | Short: what each number means, read on the D-002 latency line; Full: percentile methods (06 §7.5 toy), cost formula |
| 15 | Rate limits decide run time (Groq 8K TPM ⇒ 55 questions ≥ 14 min); throttle and resumable runs | Gate run; LLMOps notebook | **Missing** | Foundation §2.5, D2 | no | bridge | Full: the planner formula and why `results.jsonl` resumes |
| 16 | Open coding (first problem, Y/N, group later) | Task 10 | In the lab text only; the lesson cites AE Ch3 | M5 (AE Ch3) | no | bridge | Short: three sentences; say the 10 rows are a seed (AE suggests continuing to about 20 failing traces) and that the note is written **before** the stage column |
| 17 | Context swapping (give the generator the gold context) as a stage test | Telling `generate` from `retrieve` | **Missing** | M5 / V-series (`rag-evaluation`) | no | next | Full: one paragraph; costs one extra cached LLM call per item |
| 18 | Frameworks can hide or duplicate stages | G.2 | **Incomplete**: the LlamaIndex bypass is "likely"; the double retrieval and 0-based pages are not mentioned | C6 | no | core (contrast) | G.2: confirmed bypass ([C6-5]), double retrieval ([C6-4]), 0-based pages ([C6-6]) |
| 19 | The original RAG paper vs today's "RAG" | Source map ("not read") | **Missing** | C6 | no | core (background) | Short: 3 sentences ([C6-1]); Full: the hot-swap result and the two variants |
| 20 | One command from a clean environment (`uv sync --locked` + the entry point) | Gate 2→3 item 1; H.3 | Yes (H.3); the entry point is an interface assumption | O2, C6 | no | core | Keep; the LLMOps notebook calls the same entry point |
| 21 | Multi-document corpora (row ≠ `seq`, `doc_id` in citations, cross-document distractors) | Gate 2→3 item 1 (Corpus T) | Partly (D.1, H.4) | C1, C6 | no | core (blocked) | Keep H.4; the Corpus T smoke run stays blocked on DEC-3 |
| 22 | Near-ties and tie-breaking by `chunk_id` | B.2 | Yes | C4 | no | bridge | Keep (it motivates storing scores) |
| 23 | Privacy: which text may go to which API (book never; corpus D yes; Yash's own documents: a preference) | Apply-it tool; LLMOps notebook | **Missing in C6** | Foundation §2.4, D-32 (5) | n/a | bridge | One line in the tool's help and the notebook; open question §11 |

### 3. Quiz coverage

No `study/questions/C6_questions.md` exists. The lesson's own items (Part A C6-A1…A6; Part L C6-R-01, R-02, A-01…A-03, T-01) are a starting pool. Checked against what a Short version must contain:

| Existing item | Key point not answerable from a Short C6 unless added |
|---|---|
| C6-A-03 (TOY-3, "400 litres") | Needs the TOY manual and TOY-3 in Short, or a rewrite to a climate-PDF case (the toy traces live in FACTS, not in the lesson body) |
| C6-A-01 | `747bbb59942a` is a Full detail; the key point ("`params_hash` changes, ids change, rebuild; gold spans survive") must be in Short |
| C6-R-02 | "generation needs caching to repeat" (gap 11) must be in Short |
| C6-A6 | `finish_reason` and reasoning tokens (gap 12) |

Question titles still needed (format per `study/FORMAT.md`; R = recall, A = application, T = transfer):
- **R:** "What does each v0 stage write, in order?" · "What makes a rebuild trustworthy, and which two trace fields always differ?" · "What is the provenance round trip?" · "What did the 2020 RAG paper train that v0 does not?"
- **A:** "Three stages each work 9 times in 10. How often does the whole pipeline work, and when is that number wrong?" (external review §4; key: 0.729, independence, fatal failures) · "A citation resolves to nothing, but the gold page was retrieved. Which stage failed?" · "An answer is empty and `finish_reason` is `length`. What do you record and change?" · "k goes from 4 to 8. Rebuild?" · "Your p95 is 900 ms and your p50 is 160 ms on 10 queries. What can you conclude?" (06 §7.5 toy) · "A 55-question run at 8K tokens per minute: how long at least?"
- **T:** "A LlamaIndex pipeline answers well, but its FAISS index is empty. How do you find out, and why does it matter?" · "A legal assistant over 300 contracts gives a wrong date; you only have the final answer" (C6-T-01) · "Your page citations are off by one on every answer. Where do you look?"
- **Interview:** AIQ 04 Q3 "Walk me through every stage of a production RAG pipeline, from raw documents to a cited answer." (MIT, "Copyright (c) 2026 Om"), with the repo answer shown only after the attempt, then our plain-English version; and AIQ 07 Q42 (what a good trace looks like).

### 4. Errors found in existing material (not edited)

| # | Where | Problem | Evidence | Suggested fix |
|---|---|---|---|---|
| E-1 | 02 C6 card "Book"; 04 C6 row (L139) | 02 omits Ch1 p.13/14 (trade-offs table; the claim that answer quality depends entirely on retrieval) and App p.12/23 (diagnose the stage first). 04 cites only p.7 and p.10. (C6 lesson G.3 #4 reported the 04 half; still unfixed) | Pages opened 2026-10-17 | Add Ch1 p.13/14 and App p.12/23 to both |
| E-2 | 04 C6 row (L139) "two v0 runs give a byte-identical retrieval trace" | Whole records differ (`timestamp_utc`, `latency_ms`) | C6_FACTS S8; lesson G.3 #1 (still unfixed) | "identical after removing timestamp and latency" |
| E-3 | 02 C6 card and 02 §7.2; 04 L934 "FAISS store is likely bypassed (cells 9, 16)" | Now **confirmed by reading** the library: cell 13's pipeline has no embedding step, `IngestionPipeline.run` adds only nodes that already carry embeddings (and skips silently otherwise), and cell 16 builds a separate default store | [C6-5] | "is bypassed (cells 13, 14, 16; confirmed from `ingestion/pipeline.py`, not run)" |
| E-4 | C6 lesson G.2; 04 C5/C6 rows (cells 24, 28 cited as patterns) | `local_rag_huggingface_faiss.ipynb` cell 28 `RunnableParallel(answer=rag_chain, sources=retriever)` retrieves **twice** per question; the "sources" are a second retrieval, not the context the answer used | Cells 24 and 28 read; [C6-4] | Report as a pitfall; show the `.assign` pattern that retrieves once |
| E-5 | 04 P7 row ("`[Page n]` tags" as a good pattern, cells 22–24); C5/C6 reading lists | PyPDFLoader's `page` metadata is 0-based, so `[Page n]` is one less than the PDF page a reader opens | [C6-6] (current `main`; the notebook pins no version) | Add a warning; v0 uses 1-based pages |
| E-6 | C6 lesson D.3 table; lab Task 7 CHECK (cell 28 requires only `provider, model_id, cache_hit, temperature` in `llm`); `example_trace_D-002.json` | Out of date with 06 §2.5 (revised 2026-10-09), which marks `llm.max_tokens`, `llm.reasoning_effort`, `llm.finish_reason` as [N]; also lacks the Foundation E4 fields (`model_returned`, `system_fingerprint`, `reasoning_tokens`, `cached_tokens`, `http_attempts`, `cache_key`, `queue_time`) | Files read 2026-10-17 | One JSON Schema for the v0 trace; the lab CHECK, the lesson table and the example trace follow it |
| E-7 | C6 lesson D.6 "Temperature 0 does not promise identical text … (UNVERIFIED for Groq)" | Groq's API reference documents seed as best effort and determinism as not guaranteed (Foundation §2.7, its source 9) | Foundation | "Documented by Groq; not measured here" |
| E-8 | C6 lesson Source map and references: Lewis 2020 "background only; not read" | Now read ([C6-1]) | — | Use the 3-sentence comparison in Part G |
| E-9 | C6 lab Task 12 (cells 49–50); lesson Part K "Cohere + Groq for the gate run" | Calls Groq and Cohere directly, with no cache/replay layer (D-32 (7), 2026-10-17), and with `max_tokens` (Groq deprecated it for `max_completion_tokens`, Foundation E3) | Lab read; Foundation §2, E3 | Route through `study/llmops` (record once, replay after); send `max_completion_tokens` |
| E-10 | C6 lesson H.1 Task 10 vs AE Ch3 | AE wants notes before diagnosis; Task 10 asks for "first failing stage" in the same pass. Also 10 rows are below AE's stopping rule (about 20 failing traces, until no new kinds appear) | AE Ch3 'Open Coding' | Notes first, stage second; call the 10 rows a seed |
| E-11 | Gate 2→3 item 1 (02 §4); 08 Part 7 (BL-1, DEC-3) | Not an error but a block: "v0 runs on Corpus D **and Corpus T**" cannot be ticked while DEC-3 is open, so C6 cannot reach `applied` and approval gate B cannot pass | 02 §4, 08 Part 7 | Keep; propose candidates (Notes (e)); Yash chooses |
| E-12 | Book App p.7/23 puts measurement (Ch22) in Layer 5, after Layers 1–4 | The course measures right after v0 (02 principle 2), and the book's own App p.12/23 says to measure before and after each change. The lesson's G.1 row for App p.6–7 does not flag the tension | Pages opened | One line in G.1 |

### 5. What the research says

**[C6-1] Lewis et al. 2020, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"** (arXiv 2005.11401 v4, NeurIPS 2020; PDF opened and read, §2.3–2.5, §3, Tables 1, 4 and 6, §4 "Index hot-swapping", Broader Impact).
- **The study.** A BART-large generator (400M parameters) reads passages fetched by a DPR bi-encoder retriever from a December 2018 Wikipedia dump split into disjoint 100-word chunks (21M passages), searched with a FAISS HNSW index. The retriever's query encoder and the generator are **fine-tuned together** end to end, with the retrieved passage treated as a latent variable; the document encoder and index stay fixed. No supervision says which passage is right. Top k ∈ {5, 10} in training. Two variants: RAG-Sequence (same passages for the whole answer) and RAG-Token (passages can change per token).
- **The result.** Exact Match on open-domain QA: NQ 44.5 (RAG-Seq) vs DPR 41.5, REALM 40.4, closed-book T5-11B 34.5; TriviaQA 56.8/68.0 (standard / Wiki test sets); WebQuestions 45.2; CuratedTrec 52.2 (Table 1). Human raters judged RAG more factual than BART on Jeopardy question generation (42.7% vs 7.1%, Table 4). Swapping the index changes what the model knows without retraining: 70% correct on 2016 world leaders with the 2016 index, 68% on 2018 leaders with the 2018 index, but only 4–12% with the mismatched index (§4).
- **Limits.** Wikipedia only; short-answer QA metrics (EM); a trained, specialised generator, not an instruction-following chat model; the abstract itself names **provenance** (showing where an answer came from) as an open problem, and the paper outputs no citations.
- **What it means.** Today's "RAG" (and v0) is the paper's *idea* (non-parametric memory plus a generator) without its *training*: v0 uses an off-the-shelf embedder and a prompted chat model, glued by a prompt, with nothing trained together. So v0 cannot learn to retrieve better from answer errors; every improvement must be engineered and measured stage by stage. That is why C6 adds a trace: the provenance the paper left open is supplied by logging ids, pages and offsets, not by the model.
- **For this project.** Cite the paper as the origin of the term and of two lasting ideas: the index is swappable memory (hot-swap result), and the retriever matters (in their ablation, freezing the retriever lowered results on every task; swapping in BM25 lowered them everywhere except FEVER, where BM25 did best; §4 and Table 6). Do not cite its numbers as evidence for v0's behaviour: different models, data and metric. The hot-swap result is a good bridge to C3's `embed_hash`/snapshot logic (a new index = new knowledge, same model).


**[C6-2] Barnett et al. 2024, "Seven Failure Points When Engineering a Retrieval Augmented Generation System"** (arXiv 2401.05856 v1, cs.SE experience report; HTML read).
- **The study.** Three RAG builds (research, education, biomedical). The biomedical one indexed BioASQ open-access papers (4,017 documents in §4.3; the introduction says 15,000, an inconsistency in the paper) with 1,000 question–answer pairs, answered with GPT-4 and checked by an automated eval tool plus a manual look at 40 flagged issues.
- **The result.** Seven failure points: FP1 missing content (answers instead of declining), FP2 missed top-ranked documents (answer ranked below k), FP3 not in context (retrieved but dropped during consolidation), FP4 not extracted (in context, model misses it), FP5 wrong format, FP6 incorrect specificity, FP7 incomplete. Lessons: configuration must be tuned as a whole pipeline; robustness can only be fully judged while running, so monitoring is needed; adding metadata such as file name and chunk number to the context helped.
- **Limits.** Mostly qualitative: no accuracy numbers; two of the three case studies are withheld; non-expert raters; small manual sample.
- **What it means.** The FPs are a vocabulary for *where* a RAG answer fails, and nearly all sit downstream of the index. The C6 ladder (D.5) adds the two upstream stages Barnett does not name (parse, chunk) and is ordered upstream → downstream, which Barnett's list is not.
- **For this project.** Map each FP onto the ladder in the lesson (Full mode): FP2 → `retrieve`; FP3 → impossible in v0 (no consolidation step; becomes real in v4.0 with a token budget); FP4/FP7 → `generate:grounding` or a correct-but-incomplete answer (needs a human label in v0); FP1 → `generate:abstain` inverse (should have abstained: D-009, D-010); FP5/FP6 → no v0 check (open-code only). The "validation only during operation" lesson supports the monitoring page and the apply-it tool on Yash's own PDFs.

**[C6-3] OpenInference semantic conventions** (Arize, `spec/semantic_conventions.md` on GitHub main, read 2026-10-17; Foundation §3.3 and source 35 already verified the spec in general).
- **What it defines.** Span kinds `LLM`, `EMBEDDING`, `CHAIN`, `RETRIEVER`, `RERANKER`, `TOOL`, `AGENT`, `GUARDRAIL`, `EVALUATOR`, `PROMPT`, `DECISION`. Retriever spans carry `retrieval.documents.<i>.document.{id, score, content, metadata}`; embedding spans `embedding.model_name`, `embedding.text`, `embedding.vector`; LLM spans `llm.model_name` (plus `llm.request.model_name` / `llm.response.model_name`), `llm.invocation_parameters`, `llm.token_count.{prompt, completion, total}`, `llm.token_count.completion_details.reasoning`, `llm.token_count.prompt_details.cache_read`, `llm.prompt_template.{version, variables, template}`; plus `session.id`, `user.id`, `metadata`, `tag.tags`.
- **For this project.** One v0 query = one `CHAIN` root span (`run_v0`) with children `EMBEDDING` (query), `RETRIEVER` (top-4: `document.id` = `chunk_id`, `document.score`, `document.metadata` = page and offsets, **no `document.content`** unless corpus D), `PROMPT` (template `answer_v1`, version, sha256) and `LLM`. Each 06 §2.5 field maps to one attribute (table in §9). The JSONL record stays the source of truth; spans are an export view (Foundation §3.2). OTel GenAI conventions: still "Development" status and moved to their own repository (Foundation §3.3; AIQ 07 Q13 says the same): do not build the course schema on their attribute names.

**[C6-4] LangChain core source, `runnables/passthrough.py`** (GitHub master, read 2026-10-17). `RunnablePassthrough.assign(...)` merges the input dict with the mapper's output: `{**value, **mapper.invoke(value)}`; the mapper is a `RunnableParallel`. The older "how to return sources" docs (python.langchain.com v0.2) now redirect to the new docs site, so the pattern is cited from source, not the guide.
- **For this project.** The source-returning v0 chain is `RunnableParallel(context=retrieve_fn, question=RunnablePassthrough()).assign(answer=build_messages | chat | parse)`: retrieval runs **once** and its output (ids, scores, pages) travels with the answer. The repo's `local_rag_huggingface_faiss.ipynb` cell 28 uses `RunnableParallel(answer=rag_chain, sources=retriever)`, which runs the retriever **twice** (once inside `rag_chain`, once for `sources`): two query embeddings per question (two Cohere calls if uncached), and "sources" that are only *assumed* to equal the context. A good LLMOps-notebook contrast.

**[C6-5] LlamaIndex core source, `ingestion/pipeline.py`** (GitHub main, read 2026-10-17). When a `vector_store` is set, `run()` keeps only nodes whose `embedding is not None` and adds those; an empty list is skipped with no warning. The default transformations (`SentenceSplitter()` + `Settings.embed_model`) apply only when `transformations` is `None`.
- **For this project.** Confirms 02's "FAISS store likely bypassed" for `simple_rag_with_llamaindex.ipynb`: cell 13 passes an explicit list with no embedder, so no node has a vector, nothing reaches FAISS, and cell 16's `VectorStoreIndex(nodes)` silently builds a separate default in-memory store. (Verified on current `main`; the notebook pins no llama-index version, so behaviour at the notebook's date is **UNVERIFIED**, but the same filter is the documented design.) This is the best "a framework hid a stage" example for C6.

**[C6-6] langchain-community `PyPDFParser`** (GitHub main, `document_loaders/parsers/pdf.py`, read 2026-10-17). `page` metadata comes from `enumerate(pdf_reader.pages)`, so it is **0-based**; a separate `page_label` key holds the PDF's own label.
- **For this project.** The repo's `[Page n]` tags (`local_rag_huggingface_faiss.ipynb` cell 24) and C1's PyPDFLoader path print page 0 for the first page: a citation off by one against a human-opened PDF. v0 uses 1-based pages (06 §3.1). The provenance round-trip check in the apply-it tool must catch exactly this (citation page → chunk → page text contains the quoted span).

**[C6-7] Hamel Husain, "A Field Guide to Rapidly Improving AI Products"** (hamel.dev, 24 March 2025; read). Production write-up from consulting work.
- **The claim.** Reading real traces (error analysis) is the highest-return activity; let failure categories emerge bottom-up, count them with a spreadsheet or pivot table, use pass/fail plus a written critique, and build a small custom trace viewer. Example: an apartment-leasing assistant where date handling was 66% of tested failures; success went from 33% to 95% after targeted fixes (no sample size given).
- **Limits.** Anecdotal (30+ client engagements), no controlled comparisons; the post also promotes the author's course and tools.
- **For this project.** Supports C6's Task 10 (open-code 10 traces, Y/N, first problem) and argues for a **trace viewer page** that shows one v0 trace with its chunks resolved, rather than raw JSONL. It is the same method as AE Ch3 (same authors), so it is not independent evidence.

**[C6-8] Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey"** (arXiv 2312.10997, v1 2023-12-18, v5 2024-03-27; abstract read only). Names three paradigms: Naive RAG, Advanced RAG, Modular RAG. v0 is "Naive RAG" in this vocabulary (index → retrieve → generate, no pre- or post-retrieval steps). Body not read, so the exact definition is cited from the abstract only (**partly verified**). Use: interview vocabulary only.

**AE Ch3 (method, paraphrased).** Open coding: read each trace as the user would; write a short, concrete, informal note on the **first** (most upstream) problem you see, because later problems are often its consequences; add a binary acceptable/unacceptable judgement; do not diagnose causes or propose fixes yet; keep going until about 20 failing traces and no new kinds appear; do not let an LLM do the open coding (an LLM may *propose* groupings in axial coding, which you then check). Axial coding then groups notes into distinct failure modes and counts them (one 0/1 column per mode). *AE Ch3, 'Open Coding: Reading and Labeling Traces'* and *'Axial Coding: Structuring Failure Modes'*.
- **For C6.** Task 10's table follows this already (external review §3a row 7 was applied). Two gaps remain: (1) 10 queries cannot reach AE's ~20 failing traces, so Task 10 is a **seed**, and the lesson should say so; (2) AE says not to diagnose at the open-coding step, while Task 10 also asks for "first failing stage". Fix: write the note first, then fill the stage column from the ladder in a second pass, so the note is not biased by the ladder's vocabulary.

**Current practice (2024–2026), from [C6-3]–[C6-7] and Foundation §3.**
- A baseline RAG run is traced as a tree of spans (chain → embedding → retriever → prompt → LLM), with model version, parameters, token counts, finish reason, retrieved ids and scores on every request (AIQ 07 Q8, Q42).
- Frameworks hide stages (LlamaIndex `Settings` globals and the skipped vector store; LangChain retriever defaults `k=4`, `similarity`), so production teams either trace the framework's callbacks or keep the linear path in plain code.
- Error analysis on traces precedes metrics; failure counts drive what to build next ([C6-7], AE Ch3).
- Compounding: AIQ 04 Q3 (MIT, "Copyright (c) 2026 Om") says errors compound, "90% parsing quality × 90% retrieval recall × 90% faithful generation ≈ 73% end-to-end". Our own wording: if three stages each succeed 9 times in 10 **and fail independently and any failure is fatal**, the pipeline succeeds 0.9³ = 0.729 of the time. Both conditions are often false: a model answering from memory can survive a retrieval miss (06 §7.1, TOY-7), and failures cluster (hard questions fail several stages at once). So the product is a rough warning, not a prediction: measure each stage on the same questions.

**Pitfalls, with evidence.**

| Pitfall | Evidence | v0 guard |
|---|---|---|
| A framework silently skips a stage | [C6-5] LlamaIndex FAISS bypass, no warning | Plain functions; every stage writes an artifact; trace has one field per stage |
| Sources retrieved twice, not the ones used | [C6-4], repo cell 28 | Retrieve once; context ids come from the same list the prompt was built from |
| 0-based page labels | [C6-6] PyPDFParser | 1-based pages (06 §3.1); round-trip check |
| Correct answer, retrieval failed (danger zone) | 06 §7.1; C6 TOY-7 | Ladder checks retrieval before generation |
| Cut-off answer looks like a citation failure | C5 D.6; AIQ 08 Q14 via external review §3a row 5 | `length_stop`, `unexpected_finish_reason` flags (already in C6 lab printer) |
| Retries hidden in latency and cost | Foundation §2.5, E8 | `max_retries=0`, `http_attempts` in the trace |
| Logging the alias, not the version | AIQ 07 Q8 pitfall 2 | `model_requested` + `model_returned` + `system_fingerprint` (Foundation E4) |
| Rate limits stretch a run; a crash loses it | Foundation finding 5 | Token-bucket throttle; resumable `results.jsonl` |

**How to evaluate v0.** v0 has no hypothesis (06 §4.2): it is measured, not judged better or worse. Report separately: (1) **retrieval**: CE@4 on gold spans (primary), Hit@4, MRR (diagnostic), on the 06 §6.7 seeds now and the M1 set later; (2) **answers**: deterministic checks (abstention exact string, citation format, citation resolves to a context chunk, citation page-hit, EM/token-F1 for short answers, `length_stop`, empty answer) plus ≥ 30 human answer labels (D-10, 06 §8.4); (3) **ops**: p50/p95 per stage (named method), tokens, cost if called vs paid, cache hit rate. The ladder's first failing stage per trace is the bridge into M5.

**Interview questions** (titles; MIT repo items quoted with the notice above):
1. "Walk me through every stage of a production RAG pipeline, from raw documents to a cited answer." (AIQ 04 Q3)
2. "How do you evaluate a RAG pipeline? Why evaluate components separately from the end-to-end system?" (AIQ 07 Q22)
3. "What should you log for every LLM call in production, and what are the pitfalls?" (AIQ 07 Q8)
4. "Design the observability stack for a production LLM application. What does a good trace look like?" (AIQ 07 Q42)
5. Ours: "An answer is correct but cites a page that was never retrieved. Which stage failed, and how would your logs show it?"

### 6. Lesson blueprint

The existing Parts A–M lesson is strong and measured. The new study-kit lesson (`study/lessons/C6_v0_pipeline.html`, P3 order) **reuses its measured numbers** and fixes the gaps in §2 and the errors in §4. Short = enough to build and debug v0; Full = framework contrasts, spans, rate limits, the paper.

**The answer first (draft, 5 sentences).**
1. v0 is the simplest complete RAG system: it turns a PDF into numbered chunks once, then for each question it finds the 4 closest chunks and asks Groq to answer only from them, citing `[doc:page]`.
2. Its job is not to be good but to be **traceable**: every question leaves one record that names each artifact (pages, chunk ids, scores, prompt hash, answer, citations, tokens, time, cost).
3. With that record you can find the **first** stage that broke, walking from parsing to generation, instead of guessing from the final answer.
4. Retrieval is repeatable byte for byte; answers repeat only when they are replayed from the cache, so the two are always judged separately.
5. Every later version (v0.1 to v7) is measured against this baseline, which is why it must run with one command and never change silently.

**The theory in one read (12 linked ideas).**

| # | Idea | Formula or rule |
|---|---|---|
| 1 | Two phases | index: ⌈n_chunks / 96⌉ embed calls, once per corpus × config; query: 1 embed + 1 search + 1 LLM call per question (Ch1 p.13/14) |
| 2 | Every stage writes one artifact | page texts → snapshot → chunk records → `V` (n × d) → index files → ranked candidates → messages → answer + citations → trace |
| 3 | Ids are join keys, not cache keys | `chunk_id = doc_id:snapshot_id:params_hash:seq(5 digits)`; row i of `vectors.npy` = line i of `chunks.jsonl` |
| 4 | Offsets make a chunk findable | `doc_text[char_start:char_end] == text`; document offset = page start + page offset (p.10: 20,555 + 438 = 20,993) |
| 5 | A trace is one record per question (and, in Full, a tree of spans) | 06 §2.5 fields; spans CHAIN → EMBEDDING → RETRIEVER → PROMPT → LLM ([C6-3]) |
| 6 | The provenance round trip | citation `[d:p]` → `resolved = {c ∈ context : c.doc = d ∧ p ∈ c.pages}` → must be non-empty → `doc_text[a:b]` holds the claim (claim check = v5.0) |
| 7 | Which stage failed: first broken artifact, upstream first | parse → chunk → retrieve → generate:citation → generate:abstain → generate:grounding (D.5) |
| 8 | Retrieval and generation are judged apart | CE@4 = 1 iff every evidence group has an alternative whose spans lie wholly inside the top-4 chunks; correct answer + CE@4 = 0 = the danger zone |
| 9 | Errors compound, under assumptions | P(all ok) = Π pᵢ if stages fail independently and every failure is fatal; 0.9³ = 0.729 |
| 10 | Reproducibility | index files and retrieval fields byte-identical on rebuild; `timestamp_utc`, `latency_ms` always differ; answers repeat only by replay (key = sha256 of the canonical request, Foundation §2.3) |
| 11 | Ops numbers | cost = in × p_in + out × p_out (+ embed fees), "if called" vs "paid"; latency p50/p95 per stage with the method named; min run time ≥ total tokens / TPM |
| 12 | Paper vs today | Lewis 2020 trained retriever and generator together; v0 glues an off-the-shelf embedder to a prompted chat model, so it can only be improved by engineering and measuring stages |

**Formula-sheet items.** chunk id format · offset conversion · CE@k and Hit@k (one line each, link P6) · Π pᵢ with its two assumptions · cost per query · p50/p95 nearest-rank vs linear (06 §7.5: 160/900 vs 165/697.5) · run time ≥ Σ tokens / TPM (55 × 2,000 / 8,000 = 13.75 ⇒ ≥ 14 min) · trace size ≈ 2.0–2.3 KB × n (S5; grows when the E-6 fields are added).

**Step-by-step outline (running example: Corpus D, question D-002 "In what year was the Paris Agreement adopted?").** Corpus D because every C1–C5 number is measured on it and it may be sent to APIs.
1. Load and snapshot: 33 pages, 72,593 characters, `snapshot_id` `ea07572562ac` (S1).
2. Chunk: 97 chunks, `params_hash` `1ca9c5a3b548` (S2).
3. Embed and index: `V` (97, 384) for MiniLM; 149,120-byte `vectors.npy` (S3–S4). With Cohere `embed-v4.0`: 2 embed calls (97 ≤ 2 × 96), recorded once, then replayed.
4. Retrieve: top-4 pages 24, 23, 10, 6; the evidence is at rank 3 (0.438607), only 0.00008 above rank 4 (S6).
5. Prompt: 4 numbered blocks, 802 local tokens; `prompt.sha256` recorded.
6. Generate: one Groq call (`temperature 0`, `reasoning_effort low`, `max_completion_tokens` 512), recorded; `finish_reason`, tokens, latency, cost into the trace. (Real answer: *not yet run*; the lesson shows the TOY until the recorded run exists.)
7. Round trip: `[climate:10]` → chunk `…:00027` (in the context) → p.10 [0, 951) → gold [20,993, 21,092) inside it.
8. Ladder: all six checks pass → `ok`. Then the same walk on TOY-7 (correct answer, evidence never retrieved) → `retrieve`.
9. Ops line: read the D-002 latency fields and cost; say what "p95 over 10 queries" can and cannot mean.
10. One command: rebuild in a fresh process; compare (S8).

**Visuals that earn their place.**

| Visual | The one thing it shows |
|---|---|
| Two-row pipeline with the artifact and its id printed under each stage (hand SVG) | Where each join key is born, and which half runs once |
| Round-trip diagram for D-002 (citation → chunk → page → span, with the real offsets) | That a citation can be checked mechanically |
| The ladder as a vertical flow with TOY-1…TOY-7 dropped in (interactive: pick a TOY, see which check fires) | "First broken artifact" beats "last thing that looks wrong" (TOY-7) |
| Compounding slider (Plotly or inline SVG): p per stage and number of stages → Π p; a toggle for "correlated failures" | 0.729 is an assumption-laden product, not a measurement |
| D-002 score bars, ranks 1–5 (S6) | Why scores must be stored: a 0.00008 near-tie |
| Latency waterfall per stage for one recorded query (empty until the recorded run) | Which stage dominates time (Ch22 p.14/19) |

**Full only.** OpenInference span map ([C6-3]); Barnett FP mapping ([C6-2]); the LlamaIndex bypass, double retrieval and 0-based pages ([C6-4]–[C6-6]); the determinism details and replay modes (Foundation §2.7); the rate-limit planner; the interface assumptions (H.2); Corpus T multi-document cautions; the Lewis hot-swap result; context swapping as a stage test; the book's Layer-5 tension (E-12).

### 7. Verify notebook plan

`study/notebooks/C6_v0_verify.ipynb`. Framework-free; **no API call by default**; runs offline in about 30–60 s on CPU (MiniLM load ~0.4 s, 97 embeds ~2 s, two rebuilds in subprocesses). Interactive charts use Plotly.

| # | Recomputes | Data and code | Expected (from FACTS) |
|---|---|---|---|
| 1 | Snapshot, chunk count, `params_hash`, first/last ids | Corpus D, the C1/C2 reference functions (import from `ragkit` once it exists; until then from `sources/verification/C6/c6_reference_v0.py`) | `ea07572562ac`, 97, `1ca9c5a3b548` (S1–S2) |
| 2 | `vectors.npy` size from the formula, then from disk | 128 + 97 × 384 × 4 | 149,120 bytes (S4) |
| 3 | D-002 walk: offsets, recomputed scores = stored scores, gold span inside rank 3 | `V[row] @ q`, page table | ranks 24/23/10/6; 0.438607 vs 0.438527 (S6) |
| 4 | Byte-identical rebuild | two subprocess runs + `c6_compare_runs.py` logic | ALL PASS except timestamp and latency (S8) |
| 5 | The ladder on the 7 TOY traces | `toy_traces.json` | labels fingerprint `24494e44adb7c4d6`; generation-first ladder differs only on TOY-7 (S10) |
| 6 | Trace schema check | a JSON Schema for the v0 trace (06 §2.5 + E-6 fields), `jsonschema` 4.26.0 | the old `example_trace_D-002.json` **fails** on the missing `llm` fields: shows E-6 live |
| 7 | Provenance round trip on D-002 | resolver function | `[climate:10]` → `…:00027` |
| 8 | Compounding: exact Π p vs a simulation with independent and with correlated stage failures (numpy, seeded) | Monte Carlo, 100k trials | independent ≈ 0.729; correlated higher or lower depending on the correlation (illustration, TOY) |
| 9 | Run-time and cost planner for 10 and 55 questions | Foundation §6.2 prices, Groq 30 RPM / 8K TPM (plan UNVERIFIED) | 10 seeds: ≥ ~2 min, ≤ ~$0.0022; 55: ≥ 14 min, ≈ $0.015 |
| 10 | *Optional, replay only:* load the recorded Groq/Cohere v0 run from `calls.sqlite` and plot real latency and tokens | `LLMOPS_CACHE_MODE=replay` | skipped with a clear message when nothing is recorded |

### 8. Apply-it tool plan and real-world checklist

**`study/tools/v0_health_check.py`** ("does my v0 pipeline produce complete, checkable traces on MY documents?"). Same shape as `bm25_fit_check.py`: CLI plus importable `run_check()` / `render_report()`, Markdown report, ✓ / ✗ / ? verdicts.

- **Inputs:** `--docs` (PDFs, .txt, .md: Yash's own small set; book PDFs refused by `privacy.py`); `--questions` (.jsonl: `q`, optional `expect` (a short quote that proves the answer), `expect_page`, `answerable`, `id`); `--embedder {minilm, cohere}`; `--generate {groq, fake, none}`; `--cache-mode {replay, auto, record}` (default `replay`; a miss stops with the record command); `--k 4`; `--max-completion-tokens 512`; `--report`.
- **What it runs:** the v0 pipeline through the same functions as the one command (`ragkit` + `study/llmops`), writing `results.jsonl`, `config.json`, the index, and the report. No new pipeline code.
- **External calls (all cached):** Cohere embed ⌈chunks/96⌉ (index, once) + one per question (query); Groq one per question. Example: 3 PDFs × 30 pages ≈ 270 chunks (Assumption: ~3 chunks per page as on Corpus D) → 3 + 20 Cohere calls and 20 Groq calls for 20 questions; then free in replay.

| # | Check | auto / manual | How |
|---|---|---|---|
| H1 | Every trace has every required field (06 §2.5 + E-6) | auto | JSON Schema |
| H2 | Joins hold: every `chunk_id` exists; `len(V) == lines`; stored scores = `V[row] @ q` (± 1e-6) | auto | recompute |
| H3 | Rebuild determinism: same `snapshot_id`, `params_hash`, ids, file hashes | auto | build twice (embeddings from cache) |
| H4 | Provenance round trip: each citation's page exists, resolves to ≥ 1 context chunk, chunk text = `doc_text[a:b]` | auto | resolver |
| H5 | Off-by-one pages: citations that fail as written but resolve at page ± 1 | auto | count; ✗ if > 0 |
| H6 | Stage-failure label per trace (ladder) | auto when `expect` is given; ? otherwise | checks 1–3 need `expect`; 4–6 need only the trace |
| H7 | `length_stop`, empty answer, `unexpected_finish_reason` rates | auto | ✗ above 5% (Foundation §8.3 threshold) |
| H8 | Abstention: exact string on `answerable: false` items; false abstentions on answerable ones | auto | 06 §3.3 string |
| H9 | Parse health: pages with no or very little text (scanned pages, images) | auto flag + manual | open the flagged page in a viewer |
| H10 | Truncation: chunks above the embedder's input limit | auto for MiniLM (256 tokens); manual for Cohere (limit from Cohere docs) | tokenizer count |
| H11 | Ops summary: p50/p95 per stage (method named, cache hits excluded), tokens, cost if called vs paid, cache hit rate, planner estimate vs actual | auto | from traces and `calls.sqlite` |
| H12 | Open-coding sheet for 10 traces (qid, accept Y/N, first problem, then stage, evidence) | manual | the tool writes a CSV template |

**Recommendation logic.** H1, H2 or H3 fail → "pipeline bug: fix before any evaluation". H4 or H5 fail → "provenance broken: fix page numbering or citation parsing". H7 > 5% → "raise `max_completion_tokens` or check `reasoning_effort`, rerun as a new config". Otherwise report the dominant first-failing stage and its owner: parse → C1/I2, chunk → I1/I2, retrieve → R1/R3/Q1, generate → P7/V1/V3. Fewer than 10 questions with `expect` → "not enough labelled questions to say which stage dominates".

### 9. LLMOps notebook plan

`study/notebooks/C6_v0_llmops.ipynb`. Foundation §12 row "2 · C5–C6": Groq generation; LCEL chain **or** plain function over `CachedChatModel`; full v0 trace; deterministic answer checks and human labels; cost per query and p95; `answer_v1`; first golden run; monitoring page. Runs fully in `replay` once recorded.

**Framework build.**
- **Primary: the plain function `run_v0(question)`** (the one command's core). Foundation §9.1: v0 is linear (retrieve → assemble → generate) with no branch, cycle or checkpoint, so a function is clearer than a graph. **No LangGraph** in C6.
- **Side by side: the same pipeline in LCEL**, to show how production code is usually wired and to get tracing callbacks for free:
  `RunnableParallel(context=RunnableLambda(retrieve_v0), question=RunnablePassthrough()).assign(answer=RunnableLambda(build_messages) | CachedChatModel(provider="groq", model=GROQ_MODEL_ID, params=…) | RunnableLambda(parse_answer))`.
  Retrieval runs once and its candidates (ids, scores, pages) travel in the output dict ([C6-4]); contrast with the repo's double retrieval (E-4).
- **Mapping to the mechanism:** `retrieve_v0` wraps C4's `retrieve` (not `VectorStoreRetriever`, whose defaults are `k=4`, `similarity`, no scores: Foundation §9.2) with `CachedEmbeddings.embed_query` (`search_query`); `build_messages` = C5 (06 §3.3 `answer_v1`); `CachedChatModel` = Groq through the course cache; `parse_answer` = C5's citations, abstention and flags.
- **Defaults the lesson warns about:** `ChatGroq` (temperature 0.7, `max_retries` 2, no `reasoning_effort`: not used, shown read-only); `Runnable.with_retry` (not used around cached calls); `RecursiveCharacterTextSplitter` (C2 owns; not used here).
- **Equivalence test (T1):** under replay, the LCEL output and `run_v0` give identical traces (minus `timestamp_utc`, `latency_ms`) for every item: same cache keys because the requests are identical.
- **LlamaIndex:** reading only (the bypass from [C6-5] as a markdown cell). Not installed.

**Tracing.**
- Default: the JSONL trace (06 §2.5 + E-6 fields), one record per question in `experiments/E000_v0_baseline/results.jsonl`.
- Local viewer: Phoenix (`uvx arize-phoenix@20.19.0 serve`; `arize-phoenix-otel` + `openinference-instrumentation-langchain` in the project). Spans: CHAIN `run_v0` → EMBEDDING (query) → RETRIEVER (`document.id` = `chunk_id`, `document.score`, `document.metadata` = page and offsets) → PROMPT (`answer_v1`, sha256) → LLM (`llm.model_name`, `llm.invocation_parameters`, `llm.token_count.*` incl. reasoning).
- Hosted: LangSmith, **Corpus D only**, inside `tracing_context(enabled=True)` after `privacy.assert_corpus_is("D")`; never for Yash's own documents.

| 06 §2.5 field | OpenInference attribute |
|---|---|
| `qid`, `run_id`, `config_hash` | `metadata` on the CHAIN span |
| `candidates.dense[i]` | `retrieval.documents.<i>.document.{id, score, metadata}` |
| `prompt.template_version`, `prompt.sha256` | `llm.prompt_template.version`; sha in `metadata` |
| `llm.model_id`, params | `llm.model_name`, `llm.invocation_parameters` |
| tokens | `llm.token_count.prompt`, `.completion`, `.completion_details.reasoning` |
| `answer.citations`, flags, first failing stage | custom `metadata` (OpenInference has no quality fields; AIQ 07 Q13) |

**Dataset and evaluators.**
- Golden set now: the **10 Corpus D seeds of 06 §6.7** (8 answerable, 2 unanswerable) as a local JSONL with its `dataset_sha256`. All are `created_by: "llm-draft"`, which 06 §6.7 excludes from scored runs: so step 1 is Yash verifying them (relabel `llm-draft-human-verified`). Until then the run is labelled **dry run, not a result**. The M1 set replaces it later. LangSmith dataset mirror: Corpus D only.
- Tier-1 evaluators (functions with the `inputs, outputs, reference_outputs → {key, score}` signature, Foundation §10 `evals.py`), retrieval and answer kept apart:
  - retrieval: CE@4 (primary), Hit@4, MRR;
  - answer: abstention exact match; citation format regex; every citation resolves inside the context; citation page-hit vs gold pages; EM / token-F1 / "gold contained" on short answers (D-001, D-002, D-008); `length_stop`; empty answer; `unexpected_finish_reason`;
  - diagnosis: `first_failing_stage` per trace.
- Framework view: `langsmith.evaluate(target=run_v0, data=…, evaluators=[…], upload_results=False)`.
- Human labels (D-10, 06 §8.4): the notebook writes a label sheet (answer: correct / partial / wrong; per citation: supports or not; abstentions excluded from faithfulness and citation labels). The **≥ 30 labels** need ≥ 30 non-abstained answers, more than the 10 seeds; plan: label the 10 seeds now (pilot), then the first ~30 answerable M1 items when M1 exists (Gate 3→4 owns the count). Codex labels are a separate calibration set, never "human". No LLM judge (D-10).

**Experiment against the previous version.** v0 has none (06 §4.2), so the notebook runs three checks instead: (1) LCEL vs plain function: must be identical; (2) embedder arm on retrieval only: MiniLM vs Cohere `embed-v4.0` on CE@4 / Hit@4 / MRR (no Groq calls; same chunks; a new `embed_hash` index each); (3) replay determinism: the replayed run equals the recorded one byte for byte (minus time fields). The generator flip rate (`record` sample 1) belongs to M4.

**Cost, latency and token tracking.** Per stage p50/p95 (named method; cache hits excluded); tokens in / out / reasoning (check once that `reasoning_tokens ≤ completion_tokens`, external review §3a row 6); cost if called vs paid (Groq $0.075 / $0.30 per 1M; Cohere embed price **UNVERIFIED**).

| Run | Cohere embed calls | Groq calls | Tokens (est.) | Min time at 8K TPM | Groq cost (upper bound) |
|---|---|---|---|---|---|
| 10 seeds, first record | 2 (index) + 10 (queries) | 10 | ≈ 10 × (900 in + ≤ 512 out) ≈ 14K | ≈ 2 min | ≈ $0.0022 |
| 55-question set (later, M1) | 0 (index cached) + 55 | 55 | ≈ 110K | ≥ 14 min | ≈ $0.015 |
| Any rerun | 0 | 0 (replay) | 0 | seconds | $0 |

Token counts are estimates from S5's local counts (prompt 771–896, o200k_harmony), not measurements. Claude: **not used in C6**; a Claude generator would be a new experiment arm (06 §9.2, Foundation §6.4), not the baseline.

**Rate-limit planning.** Token-bucket throttle (30 RPM, 8K TPM; plan UNVERIFIED) charging prompt + `max_completion_tokens` per call (AIQ challenge 11's idea); the planner refuses a run above the daily 200K TPD; resumable by skipping qids already in `results.jsonl`.

**Prompt and config versioning.** `prompts/answer_v1.txt` frozen after first use; the trace stores `template_version` and the sha256 of the rendered messages; the cache key contains the rendered messages, so `answer_v2` is a cache miss and a new registry row. `config.json` (06 says YAML; H.2 #4) holds the resolved model id (not the `.env` name) and `max_completion_tokens`. Registry row `E000_v0_baseline` with `env.json` (lock hash).

**Monitoring page, first version** (`nox -s monitor`, offline Plotly HTML; Foundation §8.3): calls and cache hit rate, replay misses, cost per run, p50/p95 per stage, `length_stop` and empty-answer rates, first-failing-stage counts per run, CE@4 per run, `system_fingerprint` changes. `monitor.yaml` thresholds: `length_stop` > 5%, any replay miss in CI, a new fingerprint, cost over the run budget.

**Replay test in CI.** pytest marker `replay`: execute this notebook headless with `LLMOPS_CACHE_MODE=replay` and the network blocked; assert no `ReplayMiss`, and that `results.jsonl` equals the committed expected hash after dropping time fields. T1 adds the trace-schema test and the LCEL-equivalence test.

**Feedback loop.** A failure seen in the apply-it tool or the canary → an open code → (if confirmed in M5) a new golden item and dataset version → a T1/T2 regression test (`ci-cd-evals`, `error-analysis`).

**Its place in the lifecycle.** Analyze: first traces and open codes (`error-analysis`, `llm-observability`; `evals-foundations`: rule out a specification gap in `answer_v1` first). Measure: tier-1 checks and the human pilot (`code-based-evaluators`, `rag-evaluation`). Improve: none in v0; a shortlist only. dev → CI (replay + schema + equivalence tests) → monitor (the page) (`ci-cd-evals`). A trace viewer page for reading one trace with its chunks resolved (`human-review-interfaces`) is optional.

### 10. Tools, frameworks, libraries and LLMs

C6 needs **no new library for the mechanism**: everything for v0 is installed. New packages appear only in the LLMOps notebook, and they are the Foundation's (§11) pins; C6 adds none of its own.

| Purpose | Library / model / service | Version (pin) | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Parse PDFs | `pymupdf` | 1.26.7 (pinned; `snapshot_id` depends on it) | yes | yes | — | AGPL-3.0 or Artifex commercial (PyPI 1.26.7) | yes |
| Arrays, exact search | `numpy` | 2.5.3 | yes | yes | — | BSD | yes |
| Local token counts | `tiktoken` (`o200k_harmony`) | 0.14.0 | yes | yes (encoding cached) | — | MIT | yes |
| Embedder (default) | Cohere `embed-v4.0` via `cohere` | 7.2.0 | yes | no | 2 calls per Corpus D index + 1 per question; price UNVERIFIED; trial key 1,000 calls/month | MIT (SDK) | yes (D-03) |
| Embedder (fallback) | `sentence-transformers` + `all-MiniLM-L6-v2` @ `1110a243…` | 6.1.0 | yes | yes | — | Apache-2.0 | yes |
| LLM, generation (default) | Groq `openai/gpt-oss-20b` via `groq`; features used: plain chat, `reasoning_effort="low"`, `max_completion_tokens`, `finish_reason`, `usage` incl. reasoning tokens, `system_fingerprint` (Groq docs, Foundation sources 9, 11, 16) | 1.7.0 | yes | no | 1 call per question; ≈ $0.0022 per 10-seed run, ≈ $0.015 per 55 (upper bound) | Apache-2.0 (SDK) | yes (D-04) |
| LLM, Claude | `anthropic` (Haiku 5.5 / Sonnet 5.5) | 1.11.0 | no | no | not used in C6: a Claude generator is a separate experiment arm, never the baseline | MIT | yes (D-32), later |
| Trace schema check | `jsonschema` | 4.26.0 | yes | yes | — | MIT | yes |
| Data models (optional) | `pydantic` | 2.13.5 | yes | yes | — | MIT | yes |
| Tables, charts | `pandas`, `plotly` | 3.0.6, 7.1.0 | yes | yes | — | BSD, MIT | yes |
| Tests | `pytest` | 9.1.1 | yes | yes | — | MIT | yes |
| Framework core (LLMOps notebook only) | `langchain-core` | 1.6.6 (Foundation §11) | no | yes | — | MIT | yes (D-32, after the mechanism) |
| Graphs | `langgraph` | 1.2.12 | no | yes | — | MIT | **not needed for C6** (linear flow) |
| Provider integrations | `langchain-groq`, `langchain-cohere` | — | no | — | — | MIT | **not used**: conflict with groq 1.7 / cohere 7.2 (Foundation finding 4); use the `CachedChatModel` / `CachedEmbeddings` adapters |
| Hosted tracing and eval | `langsmith` | 0.14.4 | no | SDK yes; service no | free plan; Corpus D only | MIT (SDK) | yes |
| Local tracing (client) | `arize-phoenix-otel` + `openinference-instrumentation-langchain` | 0.17.2 + 0.1.78 | no | yes | — | Apache-2.0 | yes |
| Local trace viewer | `arize-phoenix` server via `uvx` | 20.19.0 | no | yes | — | ELv2 | yes, outside the lock (54 deps) |
| Local CI | `nox`, `pre-commit` | 2026.8.17, 4.6.2 | no | yes | — | Apache-2.0, MIT | yes |
| Reading only | `llama-index-core` | not pinned (GitHub `main` read) | no | — | — | MIT | read-only; never installed |

Install lines (from the Foundation; **not run**):
```text
uv add --group llmops langchain-core==1.6.6 langsmith==0.14.4
uv add --group llmops arize-phoenix-otel==0.17.2 openinference-instrumentation-langchain==0.1.78
uv add --group dev pre-commit==4.6.2 nox==2026.8.17
uvx arize-phoenix@20.19.0 serve      # on demand, not a project dependency
```

**Keys:** `GROQ_API_KEY`, `COHERE_API_KEY` (present); `LANGSMITH_API_KEY` (+ `LANGSMITH_ENDPOINT`) only for the Corpus D LangSmith view; never set `LANGSMITH_TRACING` in `.env`. Model ids from `.env` (`GROQ_MODEL_ID`, `COHERE_EMBED_MODEL_ID`) are **resolved and written into `config.json`**. Nothing heavy: no GPU, no server except the optional Phoenix process.

### 11. Open questions for Yash (preferences only)

1. **Your own documents in the apply-it tool:** may their text go to Cohere and Groq (full v0), or should the tool default to local MiniLM retrieval with generation off unless you pass `--generate groq`? (Book PDFs are refused either way.)
2. **Corpus T shortlist:** shall the C1 session propose concrete files from 06 §5.1's candidates (Lewis 2020, DPR, HyDE, Lost in the Middle, RAPTOR, plus two non-RAG papers) for you to accept or swap? Without DEC-3, Gate 2→3 and approval gate B cannot pass.
3. Optional: a small offline **trace viewer** page (one trace, chunks resolved, Y/N buttons for open coding), or is the CSV sheet enough?

---

## Concept C7: Structured-data RAG (CSV/JSON)
### 1. Sources checked

**Book pages (all opened 2026-10-17, PyMuPDF text of `chapter 2.pdf`, 11 pages):**

| Page | What it covers (paraphrase) | 02 card claim |
|---|---|---|
| Ch2 p.1/11 | The problem: customer records; a "South American countries" question; a fuzzy "sounds like consulting" question | ok (p.1–2 "why character chunking breaks tables") |
| Ch2 p.2/11 | Character chunks cut rows and mix fields (illustration); core idea: one row = one document | ok |
| Ch2 p.3/11 | Row → text card → vector picture; rows are natural chunk boundaries | not cited in 02 (should be) |
| Ch2 p.4/11 | Step 1 load rows; Step 2 **field serialization** defined, with the Sheryl Baxter row as the example | ok |
| Ch2 p.5/11 | Step 3 embed each record (claims a Chile row lands near other South American rows); Step 4 store, no overlap needed | ok |
| Ch2 p.6/11 | Preparation sketch (4 steps); the query phase is the same as Ch1 | not cited in 02 |
| Ch2 p.7/11 | Caribbean (Antigua and Barbuda) and "group consulting" examples; exact query vs semantic search illustration | not cited in 02 (it is the book's strongest claim; the lesson must test it) |
| Ch2 p.8/11 | Query sketch (6 steps); three serialisations: raw values, "Field: value", natural sentence; field names = best balance | ok |
| Ch2 p.9/11 | Star-rating picture of the three serialisations (illustrative, not measured); large tables: one vector per row, embedding cost | ok |
| Ch2 p.10/11 | When to use; overkill for exact ID lookups, numeric-only data and **aggregation** (computation, not retrieval); trade-off table | ok |
| Ch2 p.11/11 | Same pipeline as simple RAG minus chunking; row-per-record only; takeaways | not cited in 02 |

**Repo notebooks (pinned `009adba`, cells 0-based, all opened):**

| Notebook · cell | What it does | Checked |
|---|---|---|
| `simple_csv_rag.ipynb` cell 8 | `pd.read_csv('data/customers-100.csv')`, preview | yes |
| `simple_csv_rag.ipynb` cell 10 | `CSVLoader(file_path).load_and_split()`: one Document per row, then the default splitter | yes (02 ok) |
| `simple_csv_rag.ipynb` cells 12, 14 | `IndexFlatL2` + `InMemoryDocstore`; `add_documents` with `OpenAIEmbeddings()` | yes |
| `simple_csv_rag.ipynb` cell 16 | `vector_store.as_retriever()` (default k = 4); stuff chain with "say you don't know" prompt; `langchain.chains` imports | yes (02 ok) |
| `simple_csv_rag.ipynb` cell 18 | The only query: "which company does sheryl Baxter work for?" → "Rasmussen Group" | yes |
| `simple_csv_rag_with_llamaindex.ipynb` cell 3 | OpenAI `text-embedding-3-small` at 512 dims, `gpt-3.5-turbo` | yes |
| `simple_csv_rag_with_llamaindex.ipynb` cell 10 | `PagedCSVReader` via `SimpleDirectoryReader` | yes (02 ok) |
| `simple_csv_rag_with_llamaindex.ipynb` cell 11 | Prints row 1 as 12 "Column: value" lines | yes (best place to *see* the serialisation) |
| `simple_csv_rag_with_llamaindex.ipynb` cells 13, 15, 17 | `IngestionPipeline(vector_store=…)`, then `VectorStoreIndex(nodes)` with no storage context; `similarity_top_k=2`; one Sheryl Baxter query | yes |
| `json_rag.ipynb` cell 8 | Downloads Nobel prizes live from `api.nobelprize.org/v1/prize.json` (676 records in the saved output) | yes |
| `json_rag.ipynb` cell 13 | `jrag_config` of jsonpath expressions → "Year: … \| Category: … \| Laureats: […] \| Motivation: …" | yes (02 ok) |
| `json_rag.ipynb` cell 15 | `jrag.tag_list` over all records | yes |
| `json_rag.ipynb` cell 19 | `all-MiniLM-L6-v2` embeddings, 384 dims | yes (02 ok) |
| `json_rag.ipynb` cells 21, 23 | `IndexFlatL2`; one query, top 5 by L2 distance; no LLM | yes (02 ⚠ "no generation" ok) |

**Data files:**
- `upstream/RAG_Techniques/data/customers-100.csv`: 17,160 bytes, 100 rows × 12 columns (Index, Customer Id, First Name, Last Name, Company, City, Country, Phone 1, Phone 2, Email, Subscription Date, Website), no BOM, LF line ends. Measured with pandas 3.0.6 (scratch script, 2026-10-17).
- **No JSON record file exists in `data/`.** `q_a.json`, `q_a_smith.json`, `q_a_smith_short.json` are question–answer sets for other notebooks. `json_rag.ipynb` needs a live web call (cell 8).


**Measured facts about `customers-100.csv`** (pandas 3.0.6, sqlite 3.45.3 via stdlib, tiktoken cl100k; scratch scripts, 2026-10-17; these are the numbers the lesson and verify notebook rebuild):

| Fact | Value | Why it matters for C7 |
|---|---|---|
| Rows × columns | 100 × 12; every column read as text except `Index` (pandas 3 shows dtype `str`) | Dates and phones are strings until parsed |
| `Country` | 85 distinct values; most common: Solomon Islands (4) | Few rows per value, so "how many in X" answers are small |
| `Country == "Chile"` / `== "chile"` / casefold | 1 / 0 / 1 | Exact match is case-sensitive in pandas and in SQL `=`; SQLite `LIKE` is case-insensitive for ASCII (1 row) |
| South American sovereign countries present | 6 rows: Chile, Paraguay, Uruguay, Bolivia, Ecuador, Guyana. Plus 2 rows "South Georgia and the South Sandwich Islands" (in or out depends on the definition used) | The gold answer needs a written definition; 6 > k = 4, so top-4 retrieval cannot return them all |
| Caribbean candidates | 9 countries, 11 rows (Antigua and Barbuda, Bahamas, Dominica, Dominican Republic ×2, Saint Vincent and the Grenadines ×2, Anguilla, Aruba, Saint Barthelemy, US Virgin Islands); membership is definition-dependent (Bahamas) | Same: define the region list before scoring |
| Subscriptions per year | 2020: 38 · 2021: 43 · 2022: 19 (range 2020-01-13 to 2022-05-26; median 2021-03-31) | "How many subscribed in 2021?" = 43, far beyond any k: the clean "vector fails, pandas succeeds" demo |
| Duplicates that create ambiguity | First names: Sheryl ×2 (Baxter, Meyers) and 6 more; Company "Simon LLC" ×2 (different countries) | "Where is Simon LLC?" has two right answers; top-1 hides one |
| `Phone 1` formats | Mixed: dots, plain digits, `+1-`, `001-`, `(xxx)`; 57 of 100 have an `x` extension | Format issues for filters and for the PII check |
| "Column: value" serialisation (12 lines) | 250–333 chars, median 287; cl100k tokens 94–123, median 109, total 10,931 for 100 rows | Far below MiniLM's 256-token window and Cohere's limit; cost ≈ 11k tokens per full embed |
| Licence / origin | Ships in the repo under its custom **non-commercial** licence; the notebooks call it "dummy customer data" (`simple_csv_rag.ipynb` cell 6). Names, emails and phones look generated (e.g. city "East Jimmychester"); its original generator is **UNVERIFIED** | Personal study use only, like Corpus D; do not republish |

**Existing course files audited:**
- 02 C7 card (lines 423–441): pages and cells checked above; Ext "none".
- 03 lines 288, 421 (C6 → C7, no other edges) and line 523 (family table: top-k truncation, ID/phone/email noise, text-to-SQL "covered by neither source", R2 link).
- 04 row 140, Ch2 section (lines 313–336), notebook table (lines 930, 935), DV-07 (line 996).
- 06 §5 (corpora: D has no tables; no C7 corpus), §9.6 (T1/T2 tiers).
- 08 lines 124, 206, 243–245 (C7 notebooks; `load_and_split` divergence; one query each).
- `progress/concept_tracker.csv`: C7 `not_started`; its prerequisites C6, C4, P4, P5, P6 all `not_started`; R1, M2, M3, M5 `exposed`.
- `progress/misconception_log.md`: MC-005 (one-sided k) and MC-002 (query embedding) touch C7.
- No C7 lesson, lab, verification folder, reading file or question file exists (checked `concepts/`, `labs/`, `sources/verification/`, `study/`).
- `sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md`: §3a row 8 (Ext line → AIQ case study 07, two sections; compare result rows, not SQL; do not copy its `execution_match`), the C7 seed in §3b (line 118: the 'Chile' vs 'chile' empty-filter question, **CR-13-eligible: keep it out of the C7 lesson**), §8 row 30 (awaits Yash's OK).

**AI Eval book (paraphrase only):**
- AE Ch5, 'Defining the Right Metrics': *executability checks*, i.e. run generated SQL against a test database to confirm it runs and gives plausible results.
- AE Ch8, 'Why Evaluate Each Stage Separately': Uber's QueryGPT, a text-to-SQL agent evaluated per stage (intent accuracy, table overlap, execution success) plus one end-to-end query-similarity check by an LLM judge.

**Interview repo (MIT, "Copyright (c) 2026 Om", pinned `e080df2`):**
- `11-ai-system-design/case-studies/07-text-to-sql-agent.md`, 'Schema retrieval & pruning' (sample values for low-cardinality columns prevent case-mismatch filter misses) and 'Evaluation plan' (execute both queries, compare result sets; empty-result matches need manual review). Also 'Read-only enforcement & row-level security' (read-only role, single-statement SELECT only) — useful for the D4 link.
- `04-rag-and-retrieval/questions.md` Q38 (line 990): routing across structured and unstructured data. **Best interview item for C7.**
- `14-company-interview-questions/palantir.md` Q10 (line 227): "how many open orders are blocked…" — plain RAG cannot count.
- `04-rag-and-retrieval/questions.md` Q30 (line 745): tables inside documents (link to C1/I2, not C7 core).

**External sources** (numbered; details and limits in §5):

| # | Source | Status |
|---|---|---|
| [C7-1] | Sui, Zhou, Zhou, Han, Zhang. "Table Meets LLM: Can Large Language Models Understand Structured Table Data? A Benchmark and Empirical Study." WSDM 2024. https://arxiv.org/abs/2305.13062 | verified (full PDF v5 read) |
| [C7-2] | Bhandari, Singh, Gao, Dan, Gupta. "Improving Robustness of Tabular Retrieval via Representational Stability." arXiv 2604.24040, 2026. https://arxiv.org/abs/2604.24040 | verified (abstract only; no numbers) |
| [C7-3] | Yu et al. "Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task." EMNLP 2018. https://arxiv.org/abs/1809.08887 | verified (abstract) |
| [C7-4] | Li, Hui et al. "Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs" (BIRD). NeurIPS 2023. https://arxiv.org/abs/2305.03111 | verified (abstract) |
| [C7-5] | Zhong, Yu, Klein. "Semantic Evaluation for Text-to-SQL with Distilled Test Suites." EMNLP 2020. https://aclanthology.org/2020.emnlp-main.29/ | verified (full PDF read) |
| [C7-6] | SQLite `PRAGMA query_only` https://www.sqlite.org/pragma.html and Python 3.12 `sqlite3` docs https://docs.python.org/3.12/library/sqlite3.html | verified |
| [C7-7] | Groq docs, Tool use https://console.groq.com/docs/tool-use and Structured outputs https://console.groq.com/docs/structured-outputs | verified (`tool_choice` options UNVERIFIED) |
| [C7-8] | `langchain-community` `SQLDatabase` source https://raw.githubusercontent.com/langchain-ai/langchain-community/main/libs/community/langchain_community/utilities/sql_database.py | verified (main branch, 2026-10-17) |
| — | PyPI JSON API for `duckdb`, `sqlglot`, `langchain-community`, `langchain-core`, `langgraph`, `jrag` (2026-10-17) | verified |

### 2. Gap audit

Tracker check: C7 and every prerequisite it leans on (C2, C4, C6, P1, P4, P5, P6) are `not_started`; R1, M2, M3, M5 are `exposed`. So every bridge below must be taught briefly inside C7, not assumed.

| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class | How the lesson should handle it |
|---|---|---|---|---|---|---|---|
| 1 | One row = one record = one document; rows are natural chunk boundaries | Book Ch2 p.2–4/11; 02 outcome 1 | missing (no C7 lesson) | C7 | no | core | Open with it (Short) |
| 2 | Why character chunks break a table (rows cut, fields mixed) | Book Ch2 p.1–2/11; 02 failure 1 | in C2 (07), not studied | C2 | no | bridge | One picture plus a measured count of rows cut by a 1000/200 chunker on this CSV (Short) |
| 3 | Field serialisation: raw values, "Column: value", natural sentence | Book Ch2 p.4/11, p.8–9/11; 04 step 2 | missing | C7 | no | core | Three versions of row 1 side by side (Short); measured effect in the verify notebook |
| 4 | Column selection (drop IDs, phones, e-mails, URLs) | 03 line 523 (noise); 04 "build yourself" | missing; the book serialises all fields | C7 | no | core | Rule: keep columns a user would ask about by meaning (Short) |
| 5 | Query embedded with the same model; cosine; top-k | Book Ch2 p.6/11, p.8/11; MC-002 | P4/C4 lessons exist; not studied | P4, C4 | no | bridge | Three sentences plus the formula (Short) |
| 6 | **Top-k caps completeness**: Recall@k ≤ k/\|G\| when \|G\| > k | 02 failure 2; 04 DV-07; MC-005 | missing | C7 (uses C4, P6) | no | core | The key formula and chart (Short) |
| 7 | Row length in tokens vs the embedder's limit | Book Ch2 p.9/11 (cost); MC-001 | C3/P1 lessons; not studied | P1, C3 | no | bridge | Measured: 94–123 cl100k tokens per row; MiniLM limit 256 (Short, one line) |
| 8 | Question types: lookup, filter, aggregate, semantic, mixed | Book Ch2 p.10/11; 02 outcome 2 and evidence | partial in the book (no "filter" or "mixed") | C7 | no | core | The routing table (Short) |
| 9 | pandas filter, `value_counts`, `groupby`, date parsing | 02 evidence ("pandas succeeds") | **not taught anywhere in the course** | C7 | unknown | core (skill) | Four one-line recipes with outputs (Short) |
| 10 | SQL basics: SELECT, WHERE, GROUP BY, COUNT, LIMIT; a DataFrame into `sqlite3` | brief §C7 research; text-to-SQL | **not taught anywhere** | C7 | unknown | core (skill) | Same four questions in SQL beside pandas (Short) |
| 11 | Value matching: case, spaces, spellings, formats; list distinct values before filtering; an empty result is not "zero" | review §3b seed; [C7-4]; AIQ case study 07 | missing | C7 | no | core | Teach with a **different** value than Chile, because the Chile item is a CR-13 seed that must stay out of the lesson (Short) |
| 12 | Region and category questions need a written gold definition | Book Ch2 p.1/11, p.7/11 | missing | C7 (M1 owns gold sets) | no | core | The South-America list problem (6 or 8 rows) (Full) |
| 13 | Text-to-SQL by an LLM: schema + sample values in, SQL out, validate, run | brief; AIQ 04 Q38; [C7-3], [C7-4] | missing | C7 | no | core (Full) | Short: one paragraph and the flow; Full: the prompt parts and why sample values matter |
| 14 | SQL safety: read-only connection, one statement, authorizer, LIMIT, timeout | [C7-6]; [C7-8]; AIQ case study 07 | missing | D4 | no | bridge | The four layers as one table (Short); D4 owns the threat model |
| 15 | Execution match: compare result rows, not SQL text; false positives; empty matches | [C7-5]; review §3a row 8 | missing (M2/M3 not built) | C7 (M3 later) | no | core | Definition plus one false-positive example (Short); test suites in Full |
| 16 | Router: rules first, LLM fallback; a misroute looks like a retrieval failure | AIQ 04 Q38 | missing | A1 | no | bridge | One table and one warning; link A1 |
| 17 | Keep retrieval and answer quality apart | CLAUDE.md; `rag-evaluation` | P6/C6; not studied | P6, M2 | no | bridge | Row-level Recall@k for the semantic path; exact match for computed answers |
| 18 | Embedding cost of a large table | Book Ch2 p.9/11 | missing | C7 | no | core | Measured 10,931 tokens for 100 rows; scale linearly (Short, one line) |
| 19 | JSON: choose the document unit (record vs sub-record), flatten paths, the field-selection trap | `json_rag.ipynb` cells 13, 15; C7-E6 | missing | C7 | no | core | One nested example built from the CSV; the `laureates[0]` trap (Short, brief) |
| 20 | Metadata filter, then vector search (hybrid) | 03 line 523 | missing | R2 | no | next | Link only |
| 21 | Mixed answers: SQL rows + document chunks in one prompt | AIQ 04 Q38 | missing | A1 | no | next | Link only |
| 22 | Prompt injection through a cell value; PII in rows sent to an API | AIQ case study 07 failure table; `safety-evals` | missing | D4 | no | next | One warning line; link D4 |

Ideas the book teaches well and the lesson keeps (paraphrased): rows need no overlap (p.5/11), the preparation and query sketches (p.6/11, p.8/11), and "overkill" cases (p.10/11).

### 3. Quiz coverage

No question file exists. `study/questions/C7_questions.md` needs these items (titles only; ids per `study/FORMAT.md`). The "taught in" column names the lesson section (§6 outline step) that makes each answerable from **Short**.

| Id | Type · set | Title | Taught in (Short) |
|---|---|---|---|
| C7-PRE-01 | R · pre | Would you split a CSV into 1,000-character chunks? Why or why not? | step 2 |
| C7-PRE-02 | A · pre | Can top-4 vector search answer "how many customers joined in 2021"? | step 5 |
| C7-R-01 | R · main | What replaces character chunking for a table, and why is no overlap needed? | steps 1–2 |
| C7-R-02 | R · main | Name the three row serialisations and the trade-off between them | step 3 |
| C7-R-03 | R · main | Why can top-k retrieval not be complete? Give the ceiling formula | step 5 |
| C7-R-04 | R · main | Which route answers a lookup, a filter, an aggregate and a fuzzy question? | step 8 |
| C7-R-05 | R · main | What does execution match compare, and how can it pass a wrong query? | step 10 |
| C7-A-01 | A · main | Serialise this row, choosing which columns to keep, and say why | steps 3–4 |
| C7-A-02 | A · main | Route six given questions and name the tool for each | step 8 |
| C7-A-03 | A · main | Compute Recall@4 for "list the South American customers" from a ranked list | step 5 |
| C7-A-04 | A · main | Do these two result sets execution-match? (column-order trap) | step 10 |
| C7-A-05 | A · main | Write the read-only `sqlite3` connection and the LIMIT wrapper | step 9 |
| C7-T-01 | T · main | A product catalogue with long descriptions and prices: which questions go where, and what do you embed? | steps 3–4, 8 |
| C7-T-02 | T · main | Nested JSON orders: choose the document unit and the fields, and name one way data gets lost | step 11 |
| C7-R-06 | R · interview, `source=AIQ-04-Q38` | AIQ 04 Q38 verbatim (structured + unstructured routing), with the MIT notice | steps 8–10 |

Notes:
- The **scored CR-13 transfer item** is the review's C7 seed ('Chile' vs 'chile', §3b line 118). It stays in the coach-only seed bank, never in the question file or lesson.
- At most 2 external items per concept (FORMAT.md): only C7-R-06 is external.
- Key points to watch when writing answers: C7-A-03 needs the measured gold list (6 sovereign countries; say whether South Georgia counts); C7-A-04 needs the "values compared in column order" rule.
### 4. Errors found in existing material (not edited)

| # | Where | Problem | Suggested fix |
|---|---|---|---|
| C7-E1 | 02 C7 card, Failure line and Evidence line | Its own example, "how many customers in Chile?", **does not fail** on this file: the answer is 1 row, which fits in top-4, so an LLM reading 4 rows can still answer 1. The failure needs a count above k | Use a question whose answer exceeds k: "How many customers subscribed in 2021?" (43) or "List the South American customers" (6). Keep "Chile" for the casing check only |
| C7-E2 | 02 C7 card, Book line | Leaves out Ch2 p.3/11 (rows as natural boundaries), p.6/11 (preparation sketch), **p.7/11** (the region-inference claim and the exact-vs-semantic illustration, which the lab must test) and p.11/11 (row-per-record limit) | Add p.3, p.6–7, p.11 |
| C7-E3 | 04 row 140 | Book pages "p.3/11–p.9/11" omit p.1–2 (why character chunks break tables) and p.10–11 (when not to use: lookups, aggregation). 04's own Ch2 section (line 319) lists p.10–11 | Change to p.1–11/11 |
| C7-E4 | 08 line 206 ("`load_and_split` contradicts the book") | On this file the contradiction is latent, not real: `load_and_split()` runs the default `RecursiveCharacterTextSplitter` (4,000 characters, Foundation §9.2) and the longest row is 333 characters, so **no row is split**. It would split rows of wide tables or long text columns | Reword: "harmless here; splits any row above 4,000 characters" |
| C7-E5 | 02 Ext line "none"; 03 line 523 "text-to-SQL covered by neither source" | Still true for the two sources, but the review's §3a row 8 proposes the AIQ case study, and primary sources exist (Spider, BIRD; §5) | Apply review row 30 when Yash OKs it; add [C7-3], [C7-4] |
| C7-E6 | `json_rag.ipynb` cells 13, 15 (upstream, read-only) | The config comment says all laureates of a prize share one motivation, so it keeps only `laureates[0].motivation`. Cell 13's own output contradicts it: for 2024 chemistry, Baker's motivation differs from Hassabis's. Field selection silently drops data | Teach it in the lesson as the JSON field-selection trap; do not edit upstream |
| C7-E7 | `json_rag.ipynb` cell 8; 04 line 930 | The JSON data is fetched live from `api.nobelprize.org`; no JSON record file is in `data/`, so the notebook is not reproducible offline, and the data licence is **UNVERIFIED** | The C7 lab builds its JSON example locally from the CSV (nested records), so no web call is needed |
| C7-E8 | `simple_csv_rag_with_llamaindex.ipynb` cells 13, 15 | `VectorStoreIndex(nodes)` is built without a `StorageContext`, so the FAISS store from cell 8 is likely bypassed, as 02/04 already say for `simple_rag_with_llamaindex` (**UNVERIFIED**; LlamaIndex not installed) | Note it in the "read as contrast" box |
| C7-E9 | Book Ch2 p.7/11 illustration and p.5/11 | Presents semantic search as finding all matching rows. Top-k returns a fixed number of rows and no score threshold means "all", so completeness is never guaranteed. Whether the Chile row really lands near the other South American rows is a measurable claim, not a fact | The lesson states it as a claim and the verify notebook measures it (recall of the 6 rows at k = 4, 10, 20) |
| C7-E10 | Book Ch2 p.1/11 ("no SQL query can answer" the fuzzy consulting question) | Over-stated today: an LLM can turn a fuzzy concept into a list of values or a `LIKE` pattern for SQL, or label rows once at index time. The book's point (exact filters need exact values) still holds | One sentence in Full mode: "fuzzy → semantic search, or let an LLM write the value list, then check it" |
| C7-E11 | AIQ case study 07, `execution_match` (MIT; already flagged in review §3a row 8) | (a) It sorts the values **inside each row**, so it ignores which column a value came from; (b) `round_floats` is never defined; (c) it is order-insensitive even for "top 3 by date" questions | The course evaluator compares rows as tuples in a fixed column order, rounds floats explicitly, and keeps order only when the question has ORDER BY + LIMIT |
### 5. What the research says

**[C7-1] Sui et al. 2024, "Table Meets LLM" (WSDM 2024; arXiv 2305.13062v5; full PDF read).**
- *Study:* the SUC benchmark, 7 table-structure tasks (cell lookup, reverse lookup, column retrieval, row retrieval, size detection, merged cells, table partition). The whole table is put **in the prompt** and GPT-3.5 (and GPT-4 on a 300-item subset) answers. Formats compared: NL+separators, Markdown, JSON, XML, HTML.
- *Result:* HTML with format explanations and role prompts scored best overall (65.43% across the 7 tasks), 6.76% above NL+Sep. GPT-3.5 **row retrieval** (list one row's values) was only 29–42% across formats, and **size detection** (count rows and columns) 40.7–67%. Zero-shot dropped overall accuracy by 30.38%. Questions placed after the table lost 6.81%.
- *Limits:* it tests LLMs *reading* tables in the prompt, not embedding rows for search; GPT-3.5/4 only (2023 models); small benchmark tables.
- *For the project:* evidence that an LLM should not be asked to count or list rows it was shown. Counting belongs to pandas/SQL. It does **not** tell us which row text embeds best; we measure that ourselves.

**[C7-2] Bhandari et al. 2026, "Improving Robustness of Tabular Retrieval via Representational Stability" (arXiv 2604.24040v2; abstract only).**
- *Study:* the same table serialised as csv, tsv, html, markdown and ddl, embedded with MPNet, BGE-M3, ReasonIR (dense) and SPLADE (sparse), on several table-retrieval benchmarks.
- *Result (abstract):* equivalent serialisations give substantially different embeddings and rankings; averaging embeddings over formats is more stable; an adapter helps some dense encoders. No numbers on the abstract page.
- *Limits:* table-level retrieval, not row-level; abstract only (numbers **UNVERIFIED**); a recent preprint.
- *For the project:* the serialisation is a real experimental variable. The book's "field names help most" (Ch2 p.8/11, p.11/11) is a reasonable claim without a measured source, so the verify notebook measures it on our data.

**[C7-3] Yu et al. 2018, "Spider" (EMNLP 2018; arXiv 1809.08887; abstract).**
- *Study:* 10,181 questions, 5,693 unique SQL queries, 200 multi-table databases, 138 domains; **different databases in train and test**, so a model must handle unseen schemas.
- *Result:* the best 2018 model reached 12.4% exact-match accuracy on the database split.
- *Limits:* the original Spider is now saturated by LLMs (AIQ case study 07 says the same); clean, small databases.
- *For the project:* defines the task and the cross-schema idea. Our table is one tiny schema, so leaderboard numbers do not transfer.

**[C7-4] Li et al. 2023, "BIRD" (NeurIPS 2023; arXiv 2305.03111v3; abstract).**
- *Study:* 12,751 question–SQL pairs over 95 databases (33.4 GB, 37 domains), with **dirty values**, external knowledge needed to link questions to values, and query efficiency.
- *Result:* ChatGPT 40.08% execution accuracy vs humans 92.96%.
- *Limits:* 2023 models; numbers have since moved (not checked here).
- *For the project:* the gap is about **values**, not syntax: real data has odd spellings and formats. That is exactly the casing/format checklist in §8.

**[C7-5] Zhong, Yu & Klein 2020, "Semantic Evaluation for Text-to-SQL with Distilled Test Suites" (EMNLP 2020; full PDF read).**
- *Study:* 21 Spider dev-set submissions re-scored with "test-suite accuracy": run predicted and gold SQL on many generated databases, not just one.
- *Result:* single-database execution accuracy has a **6.5% mean false-positive rate** (max 9.0%; 11.0% on extra-hard queries): a wrong query happens to return the gold rows on that one database. Exact set match has a 2.6% mean false-negative rate (8.1% worst).
- *Limits:* Spider-style queries; building test suites needs a database generator.
- *For the project:* execution match on one 100-row table can pass a wrong query (e.g. `Country='Chile'` vs `City LIKE '%Chile%'` could coincide). Mitigations we can afford: compare full result rows, add 2–3 perturbed copies of the table (a cheap "mini test suite"), and flag empty-result matches for review (AIQ case study 07).

**[C7-6] SQLite and Python `sqlite3` docs (official; opened 2026-10-17).**
- *Facts:* `sqlite3.connect("file:x.db?mode=ro", uri=True)` opens read-only; a write raises "attempt to write a readonly database". `PRAGMA query_only` blocks CREATE/DELETE/DROP/INSERT/UPDATE, but the SQLite page itself says the database "is not truly read-only" (COMMIT and checkpoints still run), and any statement could switch the pragma off again. `Cursor.execute()` raises `ProgrammingError` on more than one statement. `Connection.set_authorizer()` can return `SQLITE_DENY` per action. `set_progress_handler()` aborts a long query when the handler returns non-zero.
- *For the project (our design, not the docs'):* four layers, cheapest first: (1) open with `mode=ro`; (2) an authorizer that allows only read actions (SELECT, READ, FUNCTION) and denies PRAGMA, ATTACH and every write; (3) single statement via `execute()`, and wrap the model's SQL as `SELECT * FROM (<sql>) LIMIT 200`; (4) a progress-handler timeout. This is the D4 "least privilege" idea on a laptop.
- *Measured here (sqlite 3.45.3):* `Country='chile'` → 0 rows; `Country LIKE 'chile'` → 1 row (LIKE is case-insensitive for ASCII in SQLite); `= 'Chile' COLLATE NOCASE` → 1 row. pandas `==` is case-sensitive. DuckDB's `LIKE` is case-sensitive and `ILIKE` is not (DuckDB docs; **UNVERIFIED** here, check in the notebook).

**[C7-7] Groq docs: Tool use and Structured outputs (opened 2026-10-17; also Foundation §6 sources 12–13).**
- *Facts:* `openai/gpt-oss-20b` supports local tool calling and MCP tools; **parallel tool calls are not supported**. It supports `response_format` `json_schema` with `strict: true` (constrained decoding; all fields `required`, `additionalProperties: false`). **Structured outputs cannot be combined with tool use or streaming.** `tool_choice` options are not on the page (**UNVERIFIED**).
- *For the project:* use structured output, not tool calling, for the two LLM steps: the router returns `{"route": "semantic"|"filter"|"aggregate"|"lookup"|"both", "reason": …}`, and text-to-SQL returns `{"sql": …, "assumptions": […]}`. One call each, schema-validated, cached. Tool calling is shown only if the LangGraph agent variant is built.

**[C7-8] `langchain-community` `SQLDatabase` source (`utilities/sql_database.py`, main; opened 2026-10-17).**
- *Facts:* `sample_rows_in_table_info=3` by default, so `get_table_info()` puts 3 real rows of every table into the prompt; `run()` fetches all rows (no LIMIT) and truncates strings to 300 characters; it runs **any** statement inside `engine.begin()`, with no read-only check.
- *For the project:* these are the hidden defaults the LLMOps notebook must name (§9). The course tool wraps `sqlite3` itself instead.

**Current practice (2024–2026), in short.** Production systems route by what the answer is made of: counts, filters and exact figures to SQL; meaning and fuzzy matching to vector search; both when mixed (AIQ 04 Q38; AIQ case study 07; Palantir Q10). Text-to-SQL quality is won by giving the model the right schema slice **plus sample values** of low-cardinality columns, then executing under a read-only, user-scoped role with a row cap. Evaluation compares result sets, not SQL text, on your own golden set (AIQ case study 07; [C7-5]). Row-as-document vector search survives for fuzzy questions and for prototypes (book Ch2 p.10/11).

**Pitfalls, with evidence.**
1. **Top-k truncation:** retrieval returns k rows, so any "list all / how many" answer above k is silently wrong (measured: 2021 subscriptions = 43 rows vs k = 4; 04 DV-07).
2. **LLMs count badly from context:** GPT-3.5 size detection 40.7–67%, row retrieval 29–42% ([C7-1]).
3. **Value mismatch:** case, spelling and format differences give empty or partial filters ([C7-4] dirty values; AIQ case study 07 sample-values bullet; 'Chile'/'chile' measured).
4. **Execution-match false positives:** 6.5% mean on Spider with one database ([C7-5]); empty results match each other trivially.
5. **Serialisation sensitivity:** the same row in another format embeds differently ([C7-2]); ID, phone and e-mail columns add noise tokens (03 line 523).
6. **Unsafe execution:** framework SQL tools run any statement by default ([C7-8]).
7. **Ambiguous keys:** duplicate names (Sheryl ×2, Simon LLC ×2 measured) make "the" answer ambiguous; top-1 hides it.
8. **JSON field selection drops data silently** (json_rag cell 13, C7-E6).

**How to evaluate.** Keep the two paths apart (`rag-evaluation`):
- *Semantic path (retrieval):* row-level Recall@k and Hit@k against a pandas-computed gold set of row ids. Completeness = |retrieved ∩ gold| / |gold|.
- *SQL/pandas path:* execution match on result rows (tuples in column order, multiset; order kept only for ORDER BY + LIMIT), plus "executes without error" (AE Ch5 executability check) and an empty-result flag. Stage metrics as in AE Ch8 (QueryGPT): router accuracy vs hand labels, then SQL execution success, then result match.
- *Answer:* exact match for numbers and short lists; no judge needed (D-10 untouched).
- *Baseline:* the book's pure vector route at k = 4.

**Interview questions (3–5).**
1. AIQ 04 Q38: structured + unstructured routing (MIT; verbatim allowed with notice).
2. Palantir Q10: why plain RAG gets "how many open orders…" wrong.
3. "How do you evaluate text-to-SQL when many queries are correct?" (AIQ 04 Q38 follow-up; [C7-5]).
4. "How do you stop generated SQL from writing or leaking?" (AIQ case study 07 read-only section; [C7-6]).
5. "When would you still embed rows?" (book Ch2 p.10/11).
### 6. Lesson blueprint

**Running example and why it is not Corpus D.** Corpus D (the climate PDF) has no tables (06 §5.1: `find_tables` finds none), so it cannot show this concept. C7 uses the side corpus `upstream/RAG_Techniques/data/customers-100.csv`:
- it is the book's own example (row 1 is the Sheryl Baxter row on Ch2 p.4/11 and p.8/11), and both repo CSV notebooks load it;
- it is dummy data (`simple_csv_rag.ipynb` cell 6), so no real person is involved; it ships under the repo's non-commercial licence, so personal study only, never republished;
- 100 rows is small enough to check every answer by hand.

The JSON example is built **locally** from the same CSV (customers nested under their country), so no web call is needed (C7-E7). The Nobel JSON of `json_rag.ipynb` is read-only reading.

**The answer first (draft, 5 sentences).**
1. A table already has natural chunks: one row is one record, so you turn each row into a short "Column: value" text and embed that, instead of cutting the file into character chunks.
2. That gives you search by meaning over rows, which helps when users do not know the exact values ("companies that sound like consulting").
3. But vector search returns only the top k rows, so it can never promise "all" rows, and it cannot count, sum or average.
4. So you route each question: exact lookups, filters and aggregates go to pandas or SQL, which compute the answer; fuzzy questions go to vector search; mixed questions use both.
5. When an LLM writes the SQL, run it read-only with a row limit, and judge it by comparing the rows it returns with the right rows, not by comparing SQL text.

**The theory in one read (12 linked ideas).**

| # | Idea | Formula or rule |
|---|---|---|
| 1 | Row as document | `doc_i = serialise(row_i, columns, template)` |
| 2 | Three templates | raw `v1 v2 …` · labelled `c1: v1\n c2: v2` · sentence `"{first} {last} works at {company} in {city}, {country}."` |
| 3 | Column selection | drop a column when it has no meaning to search by (IDs, phones, e-mails, URLs); hint: `nunique/n ≈ 1` and no spaces |
| 4 | Length check | `tokens(doc_i) ≤ max_seq_length` of the embedder (MiniLM 256; measured rows 94–123 cl100k tokens) |
| 5 | Retrieval | `score_i = cos(e(q), e(doc_i))`; return top-k (bridge to C4) |
| 6 | **Completeness ceiling** | `Recall@k = |topk ∩ G| / |G| ≤ min(k, |G|) / |G|`; for 2021 sign-ups `4/43 ≈ 0.09` at k = 4 |
| 7 | Question types | lookup (one known key) · filter (all rows matching a condition) · aggregate (count, sum, mean, max) · semantic (meaning, fuzzy) · mixed |
| 8 | Computing instead of retrieving | pandas `df[df.Country == v]`, `.value_counts()`, `groupby().size()`; SQL `SELECT COUNT(*) … WHERE … GROUP BY …` |
| 9 | Value matching | compare `norm(v) = v.strip().casefold()`; list distinct values first; **an empty result is a question, not an answer** |
| 10 | Text-to-SQL | LLM input = question + schema + sample values of low-cardinality columns; output = one SELECT; validate → run → answer from rows |
| 11 | Safe execution | read-only connection · one statement · allow only reads · `LIMIT` · timeout |
| 12 | Execution match | `match = multiset(rows_pred) == multiset(rows_gold)` (rows as tuples in column order; order kept only for ORDER BY + LIMIT); can pass a wrong query on one database ([C7-5]: 6.5% mean on Spider) |

**Formula sheet items.** Completeness ceiling (6); Recall@k and Hit@k at row level; execution match (12); embedding tokens `Σ tokens(doc_i)` (10,931 for 100 rows; ×1,000 rows → ×1,000 tokens); value normalisation (9); the routing table (7).

**Step-by-step outline (one running example).**
1. **Look at the table.** 100 rows × 12 columns; types; distinct counts (Country 85). (Short)
2. **Cut it the wrong way.** Chunk the raw CSV text at 1000/200 characters and count the rows split across chunks (number from the verify notebook). Then one row per document. (Short)
3. **Serialise row 1 three ways** (raw, labelled, sentence), plus token counts. (Short)
4. **Choose columns.** Keep name, company, city, country, subscription date; drop Customer Id, phones, e-mail, website. (Short)
5. **Search by meaning, then measure.** "Customers in South American countries": gold = 6 rows (sovereign list; say the definition). Recall@4 cannot exceed 4/6. "How many customers subscribed in 2021?": 43; top-4 gives at most 4 rows. Chart: Recall@k vs k for |G| = 6 and |G| = 43. Results filled only from the verify notebook. (Short)
6. **Compute instead.** pandas: 43. The same question in SQL on an in-memory `sqlite3` table: 43. (Short)
7. **Check values before you trust a filter.** Use a value **other than Chile** (for example a lower-case "netherlands" or a date typed as "2021/03/31"): `==` gives 0 rows, the normalised compare gives the true count. Show SQLite `LIKE` vs `=` vs `COLLATE NOCASE`. (Short)
8. **Route five question types** (the 02 evidence): lookup "Which company does Sheryl Baxter work for?" (note: two Sheryls, so use the full name), filter, aggregate, semantic ("companies that sound like consulting"), mixed. (Short)
9. **Run SQL safely.** `mode=ro`, authorizer, single statement, `LIMIT`, timeout; one blocked INSERT and one blocked PRAGMA shown. (Short: the table of layers; Full: the code)
10. **Let an LLM write the SQL** (Full; recorded Groq calls replayed): prompt parts, one good and one wrong query, execution match on result rows, the empty-result flag. (Short: one paragraph and the flow diagram)
11. **JSON.** Nest the CSV by country; choose the unit (one customer); flatten paths; show the `laureates[0]` trap from `json_rag.ipynb`. (Short: brief)
12. **When to embed rows at all.** Book Ch2 p.10/11 list, plus the routing rule. (Short)

**Visuals that earn their place.**
| Visual | The one thing it shows |
|---|---|
| SVG: a CSV cut by character windows vs one card per row | Character chunks mix records; rows do not |
| SVG: row 1 in three serialisations, with token counts | Labels tell the embedder what each value is |
| Plotly: Recall@k vs k for \|G\| = 6 and \|G\| = 43 (ceiling line plus measured MiniLM curve) | Top-k cannot be complete when the answer has more rows than k |
| SVG: router decision tree (lookup / filter / aggregate / semantic / mixed) | Route by what the answer is made of |
| SVG: four safety layers as a stack | No single layer is enough; the prompt is not a layer |
| Small table: two result sets that match by accident | Execution match can pass a wrong query |

**Full only.** Text-to-SQL prompt design and sample values; Spider/BIRD numbers and why leaderboards do not transfer; test-suite accuracy; the Sui et al. format results (LLMs reading whole tables); serialisation sensitivity [C7-2]; the region-definition problem (6 vs 8 rows); DuckDB as an alternative engine; the LangChain `SQLDatabase` defaults; the LlamaIndex notebook's bypassed FAISS store.

### 7. Verify notebook plan

`study/notebooks/C7_structured_verify.ipynb` (framework-free; Plotly charts).

| Block | Recomputes | Data and code | API calls |
|---|---|---|---|
| A. Profile | every number in §1's data table (shape, distinct counts, Chile/chile, per-year counts, duplicates, phone formats) with `assert`s | pandas | none |
| B. Character chunking | rows cut across chunk boundaries at 1000/200 (and 500/100) using the course C2 chunker on the raw CSV text | course chunker | none |
| C. Serialisations | 4 arms: raw, labelled (all 12 columns), labelled (chosen columns), sentence; token counts with tiktoken and the MiniLM tokenizer | plain Python | none |
| D. Retrieval | ~12 questions with pandas-built gold row ids (South America with a written list, Caribbean list, Sheryl Baxter, Simon LLC, "Group" companies, 2021 sign-ups…); Recall@k, Hit@k for k = 1, 4, 10, 20 per arm; Plotly curve with the ceiling line | MiniLM (local, cached by content as in C3) | none by default; optional Cohere `embed-v4.0` arm via the cache: 100 rows in 2 calls (96 per call) + ~12 query calls ≈ 14 calls, ≈ 11k document tokens |
| E. Counting | for 5 count/list questions: answer from top-4 rows vs pandas vs `sqlite3` | pandas, `sqlite3` | none |
| F. Value matching | `==`, casefold, `LIKE`, `COLLATE NOCASE` on a non-Chile value | pandas, `sqlite3` | none |
| G. Execution-match evaluator | unit tests: same rows other order (match), swapped columns (no match), floats rounded, ORDER BY + LIMIT (order kept), both empty (flagged); shows why sorting values inside a row (AIQ `execution_match`) is wrong | plain Python | none |
| H. Safety | `mode=ro` blocks INSERT; authorizer denies PRAGMA and ATTACH; two statements raise `ProgrammingError`; LIMIT wrapper caps rows; progress-handler timeout stops a cross join | `sqlite3` | none |
| I. JSON | nest the CSV by country; flatten; compare "record" vs "country group" as the unit on 3 questions | plain Python + MiniLM | none |

Runs offline in under about a minute on CPU (MiniLM over 100 short rows; **assumption**, measure). No LLM calls. All results tables stay empty in the lesson until this notebook's logged run fills them.

### 8. Apply-it tool plan and real-world checklist

`study/tools/structured_route_check.py` ("route my question" checker).

- **Inputs:** a CSV, JSON or JSONL path; optional `--questions questions.txt` (one per line, optional `|label` for hand routes); `--k 4`; `--embedder minilm|cohere` (default `minilm`, local); `--json-unit <jsonpath>` for JSON.
- **Outputs:** a Markdown report to stdout and `--out report.json`: column profile, per-question route with its reason, and the checklist below with pass/warn/fail.
- **No API calls by default.** An optional `--llm-router` uses Groq through the cache (`auto` or `replay`). It is off by default because rows may hold personal data (check 11).

**Real-world checklist.**
| # | Check | Auto / manual |
|---|---|---|
| 1 | Row count, column types, and columns that are text but look like dates or numbers | auto |
| 2 | Casing or spacing variants inside a column (values that collide after `strip().casefold()`) | auto |
| 3 | **Empty-result check:** each value named in a question matches 0 rows exactly but ≥ 1 row after normalising or by close spelling | auto |
| 4 | Mixed date formats (share of values `pd.to_datetime` parses; formats seen) | auto |
| 5 | Units or currency inside numbers ("12 kg", "$1,200") | auto |
| 6 | Identifier-like columns to leave out of the text (`nunique/n ≥ 0.95`, no spaces) | auto |
| 7 | Serialised row length vs the embedder limit (MiniLM 256 tokens; Cohere limit from Foundation §6.2) | auto |
| 8 | Embedding size of the whole table (total tokens; cost only if a checked price exists) | auto |
| 9 | Questions whose answer may exceed k ("all", "list", "how many", or a filter whose pandas count > k) | auto |
| 10 | Duplicate keys that make "the" answer ambiguous (names, companies) | auto |
| 11 | Personal data columns (e-mail, phone patterns): decide before any row goes to an API or a hosted trace | auto detect, manual decision |
| 12 | JSON: arrays where only the first item is kept, and fields left out of the template | auto |
| 13 | Mixed questions that need both a computed figure and text evidence | manual (read the flagged ones) |

**Recommendation logic (per question, rules first).**
1. Mentions count, sum, average, max/min, "how many", "top N" → **aggregate → pandas/SQL**.
2. Names a value found in a column (after normalising) → **filter → pandas/SQL**; if "list"/"all", warn when count > k for vector search.
3. Names an ID-like value → **lookup → pandas/SQL**.
4. Uses a category the data does not store (region, "sounds like", "similar to") → **semantic → vector search over chosen columns**, with a completeness warning; suggest "LLM writes the value list, you check it, then SQL" as the complete option.
5. Both a figure and a reason → **mixed → both paths**.
6. Table level: if most questions route to compute, report "build the SQL/pandas path first; a vector index is optional".

### 9. LLMOps notebook plan

`study/llmops/notebooks/C7_structured_llmops.ipynb` (after the verify notebook). Applies Foundation §12 row "2 · C7".

**Framework build (LangGraph, because the flow has a run-time branch and a retry cycle; Foundation §9.1).**
| Node | Lesson step | Implementation |
|---|---|---|
| `classify` | step 8 | rules first; if unsure, `CachedChatModel` (Groq `openai/gpt-oss-20b`, `reasoning_effort="low"`, `max_completion_tokens` ≥ 512) with a strict `json_schema` output `{route, reason}` |
| `semantic_retrieve` | steps 3–5 | `CachedEmbeddings` (Cohere `embed-v4.0`, MiniLM fallback) + the course NumPy retriever wrapped as a LangChain retriever; k from config |
| `text_to_sql` | step 10 | `CachedChatModel` with strict `json_schema` `{sql, assumptions}`; prompt = schema + sample values |
| `validate_sql` | step 9 | single statement; dry run under the authorizer; on failure, loop back to `text_to_sql` with the error (max 2 retries) |
| `run_sql` | step 9 | a course `@tool` over `sqlite3` (`mode=ro`, authorizer, `LIMIT 200`, timeout); returns rows + column names |
| `answer` | step 12 | computed answers are formatted by code (no LLM); semantic answers use the C5 grounded prompt over the retrieved rows |

Structured outputs and tool calling cannot be combined on Groq ([C7-7]), so the nodes use structured output and call the SQL tool from code. A second, optional arm shows the same flow as a tool-calling agent (no parallel calls on gpt-oss-20b).

**Framework defaults the lesson warns about.**
- `SQLDatabase` (`langchain-community`): 3 sample rows of every table in the prompt; any statement runs, inside a committing transaction; all rows fetched; strings cut at 300 characters ([C7-8]). Shown in a read-only cell, not used.
- `VectorStoreRetriever` default `k=4` (Foundation §9.2): the completeness ceiling in disguise.
- `ChatGroq` defaults (Foundation §9.2): not used; the adapter sets every parameter.

**External calls (all cached; the notebook runs in `replay` with no key).**
| Call | Provider · model | Count per full run |
|---|---|---|
| Router fallback | Groq `openai/gpt-oss-20b` | ≤ 25 (only questions the rules cannot place) |
| Text-to-SQL + retries | Groq `openai/gpt-oss-20b` | about 15 SQL questions × up to 3 attempts ≤ 45 |
| Semantic answers | Groq `openai/gpt-oss-20b` | about 5 |
| Row and query embeddings | Cohere `embed-v4.0` | 2 (100 rows) + ≤ 25 queries |
| Optional comparison arm | Claude Haiku 5.5 for text-to-SQL | ≤ 45, only with credits |

Cost per run (assumed ~1,000 input + ≤ 1,024 output tokens per Groq call, Foundation §6.2 prices): about 75 × (1,000 × 0.075 + 1,024 × 0.30)/10⁶ ≈ **$0.03**; the Haiku text-to-SQL arm, 45 × (1,000 × 0.10 + 1,024 × 0.50)/10⁶ ≈ $0.03. Time is set by Groq's 8K TPM (plan UNVERIFIED): about 75 × 2,000 tokens ≈ 19 minutes at least, so the run resumes from cache.

**Tracing.** Default: the course JSONL trace (Foundation §3.2) with C7 spans: route decision and reason, rule vs LLM, SQL text per attempt, validation errors, row count, first 20 result rows, `row_cap_hit`, `empty_result`, retrieved row ids with scores, tokens incl. reasoning, latency, `cache_key`. Local viewer: Phoenix. **LangSmith: needs a decision.** Foundation §3.2 allows hosted tracing for Corpus D only; `customers-100.csv` is dummy data but not Corpus D (Open question 1).

**Dataset and evaluators.** `C7_eval_v1.0.jsonl`, about 25 hand-written items (lookup 4, filter 5, aggregate 6, semantic 4, mixed 3, unanswerable 3 such as "What is Sheryl Baxter's revenue?" where no column exists). Each item: question, route label, gold SQL, gold rows (computed by pandas, stored with the dataset hash), gold answer. Kept separate from `D_eval`. Code evaluators only (D-10 untouched):
- router accuracy vs the hand label (stage 1, `tool-use-evaluation`);
- SQL executes without error (AE Ch5 executability);
- execution match on result rows (§6 idea 12), with empty matches flagged for review;
- row-level Recall@k for semantic items (`rag-evaluation`);
- exact match of the final number or list;
- correct refusal on unanswerable items;
- safety set (5 items): write attempts, PRAGMA, ATTACH, a cell value carrying an instruction — all must be blocked (`safety-evals`).

**Experiment against the previous version.** Arms on identical items: (a) the book's route: vector only, k = 4 (C6-style baseline); (b) rules router + pandas/SQL by hand-written templates; (c) LLM text-to-SQL prompt v1 (schema only); (d) prompt v2 (schema + sample values). Report per category; with ~25 items, report counts and paired differences, not significance claims (06 §9.4).

**Cost, latency, tokens.** Per stage p50/p95 (excluding cache hits), calls per question, retries histogram, reasoning-token share, cost if called vs paid (Foundation §6.1).

**Prompt and config versioning.** `prompts/c7_router_v1.txt`, `prompts/c7_text2sql_v1.txt`, `_v2`; `configs/c7.yaml` holds k, template, chosen columns, sample-values on/off, router rules version, LIMIT and timeout. Each change is one pre-registered run (Foundation §7).

**Monitoring and feedback.** Watch: empty-result rate, row-cap hits, SQL error rate, retries per question, share routed by the LLM, schema hash changes. Alert when any rate doubles against the last champion run. A flagged failure goes to the error-analysis log (misroute / wrong SQL / value mismatch / truncation), then to the golden set as a new version, then to a T1 test (rules, evaluators, safety) or a **T2** test (text-to-SQL regression, needs a key; replayed in CI).

**Place in the lifecycle and skills.** Analyze: read traces by route (`error-analysis`, `trace-data-analysis`). Measure: stage metrics and execution match (`code-based-evaluators`, `tool-use-evaluation`, `rag-evaluation`). Improve: sample values, rules, column choice (`improving-llm-agents`). CI and monitoring: T1 + T2 (`ci-cd-evals`). Tracing (`llm-observability`). Safety set (`safety-evals`).
### 10. Tools, frameworks, libraries and LLMs

| Purpose | Library / model / service | Version (pin a released version ≥ 2 weeks old) | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|
| Table loading, filters, aggregates | `pandas` | 3.0.6 (keep) | yes | yes | — | BSD-3 | yes. Note pandas 3 reads text columns as dtype `str` |
| SQL engine | `sqlite3` (stdlib; SQLite 3.45.3 measured) | stdlib | yes | yes | — | public domain / PSF | yes (default engine) |
| Alternative SQL engine | `duckdb` | 1.5.6 (2026-09-28; 13.2 MB win wheel) | no | yes | — | MIT | optional; not needed for 100 rows. Show only in Full |
| SQL parse/transpile check | `sqlglot` | 30.21.0 (2026-09-30) | no | yes | — | MIT | optional; the `sqlite3` authorizer already enforces read-only |
| Token counts | `tiktoken` | installed (keep) | yes | yes | — | MIT | yes |
| Local embeddings (verify, apply-it default) | `sentence-transformers/all-MiniLM-L6-v2` via `sentence-transformers` 6.1.0 | installed | yes | yes (after first download) | — | Apache-2.0 | yes (fallback, D-03) |
| API embeddings | Cohere `embed-v4.0` via `cohere` 7.2.0 | keep | yes | no | ≈ 2 + 25 calls per LLMOps run; ≈ 11k document tokens; price UNVERIFIED (Foundation §6.2) | MIT (SDK) | yes (default) |
| Router fallback, text-to-SQL, semantic answers | Groq `openai/gpt-oss-20b` (strict `json_schema` ✓; tool use ✓, no parallel calls; not both at once) | via `groq` 1.7.0 | yes | no | ≤ 75 calls/run ≈ $0.03; ≈ 150k tokens ≈ 19 min at 8K TPM and 75% of 200K TPD (plan UNVERIFIED) | Apache-2.0 (SDK) | yes |
| Text-to-SQL comparison arm | Claude Haiku 5.5 `claude-haiku-5-5`, effort `low`, no `temperature` | `anthropic` 1.11.0 | no | no | ≤ 45 calls ≈ $0.03; only with credits | MIT (SDK) | yes (D-32), optional. Larger models are not worth it at this size |
| Graph (router + retry cycle) | `langgraph` | 1.2.12 (Foundation §11) | no | yes | — | MIT | yes, LLMOps notebook only |
| Messages, tools, retriever wrapper | `langchain-core` | 1.6.6 (Foundation §11) | no | yes | — | MIT | yes |
| Framework SQL utilities (read only) | `langchain-community` `SQLDatabase` | 0.4.2 (2026-05-22; pulls SQLAlchemy) | no | yes | — | MIT | **not installed**: unsafe defaults ([C7-8]); show the source in a markdown cell |
| JSON field selection (repo) | `jrag` | 0.0.1 (2025-04-13; needs `jsonpath-ng`) | no | yes | — | MIT | not needed; plain Python dict paths do the same |
| Hosted tracing | `langsmith` | 0.14.4 (Foundation §11) | no | SDK yes | free plan | MIT (SDK) | **needs a decision** for this side corpus (Open question 1) |
| Local tracing | JSONL trace + `arize-phoenix-otel` 0.17.2; viewer `uvx arize-phoenix@20.19.0 serve` | Foundation §11 | no | yes | — | Apache-2.0 / ELv2 | yes (default) |
| Tests | `pytest` | 9.1.1 | yes | yes | — | MIT | yes |

Install lines (**not run**; the Foundation lines already cover the framework group):

```text
uv add --group llmops langchain-core==1.6.6 langgraph==1.2.12 langsmith==0.14.4 arize-phoenix-otel==0.17.2   # from Foundation §11
uv add --group llmops anthropic==1.11.0                                                                       # only when Claude credits exist
# optional, only if Full mode shows DuckDB:
uv add duckdb==1.5.6
```

Keys: `GROQ_API_KEY` and `COHERE_API_KEY` (present). `ANTHROPIC_API_KEY` only for the optional arm. `LANGSMITH_API_KEY` only if Open question 1 is "yes". The verify notebook and the apply-it tool need **no key**.

### 11. Open questions for Yash (preferences only)

1. May C7 traces of the dummy customer CSV go to LangSmith, or should C7 stay local-only (JSONL + Phoenix)? Recommended: **local** (the Foundation's hosted rule is Corpus D only).
2. Show DuckDB beside `sqlite3` in Full mode? Recommended: **no** (one engine is enough at this size; DuckDB is a later, optional add).

---

## Phase-level notes

### Build order inside Phase 2

1. **The helper package first.** `study/llmops/` (Foundation §10) must exist before any Phase 2 LLMOps notebook that calls an API (C3–C7). It also comes before the corrected C6 gate run, because that run must go through the cache (gap 2 in the Summary).
2. **Bridges or prerequisites.** 03's hard edges are P1 → C2, P5 → C3 and P7 → C5, and none of those prerequisites is studied. The C lessons carry the bridges in Short mode, as each §2 lists. Studying P1's tokenizer lab before C2, and P7 before C5, would close MC-001 and MC-003 faster, because a misconception closes only after two check items on different days.
3. **Record once, replay everywhere.**
   - C3 records the 97 `search_document` vectors for Corpus D.
   - C4 reuses them with the same cache keys, so its Cohere arm needs no new chunk calls.
   - C5's arm A0 and C6's seed run send identical `answer_v1` requests for the same 10 seeds, so they share cache keys. Whichever notebook runs first records them, and the other replays them. C6 is the natural owner, because its gate run is the first real Groq run.
4. **One schema and one evaluator module.** C5's `make_record` and C6's `make_trace` emit one v0 trace schema, backed by `jsonschema`. The tier-1 evaluators live once, in `llmops/evals.py`. C5's notebook stops at "answer record plus evaluators" on a fixed top-4; C6 does the end-to-end trace.
5. **Corpus T before Gate 2→3, and its cleaning rules before M1.** If a cleaning version for T is adopted after M1 labelling starts, every gold span must be re-validated (06 §5.3 rule 2).
6. **C7 is a sidebar.** It depends on C6, but it also uses C4's top-k and P6's Recall@k. Schedule it after C6 and teach those two as bridges inside C7.

### Facts the concepts disagree on (resolve once, for the whole course)

| Topic | What the helpers found | Resolution proposed |
|---|---|---|
| Cohere `embed-v4.0` input limit | C2 and the Foundation cite the docs: 128k tokens. C3 found that the Models API (O2 report) says 8,192 | **UNVERIFIED** either way. v0's 1,000-character chunks fit under both. The C3 verify notebook settles it with 2 recorded calls. Until then, set `truncate="NONE"` so an over-long input fails loudly instead of being cut silently |
| Token counts behind 07 D.6 | 07 measured them on PyPDFLoader text. C3 planned to re-measure on PyMuPDF | **Settled by C2.** A local run of the 07 chunker on the PyMuPDF snapshot gives identical numbers (97/65/65 chunks; 0/4/32 chunks over 256 MiniLM tokens). C3 can cite it rather than repeat it |
| `params_hash` recipe | The C2 lab and Gate 2→3 hash the 06 `chunking:` block; C3's measure script and 07 H.3 build it differently | Decision 2 in the Summary |
| Page numbers | The repo's PyPDFLoader `page` metadata and `[Page n]` labels are 0-based (C1, C5, C6). The course is 1-based | C1's parser tests own the check; the C5 and C6 tools only detect it |
| The `"\n\n"` separator | C1's probe found no `"\n\n"` inside any page of the 8 candidates, the same as in Corpus D | So with `scope: per_page`, C2's first separator never fires on T, and splits fall to layout line ends. Say this in C2 and plan for it in I2 |

### Corrections proposed for the Foundation (reported; `LLMOPS_FOUNDATION.md` not edited)

- **§9.2, three new rows** (C4 `E-C4-5`):
  - LangChain retrievers return documents without scores.
  - `similarity_score_threshold` fails on `InMemoryVectorStore`; this was read in the source, not run.
  - Ties have no defined order.
- **§3.3 and D1.** The LangChain OpenInference instrumentor records neither `document.id` nor `document.score`, and it exports chunk text. Every LLMOps notebook with a retriever should therefore write its own RETRIEVER span (C4).
- **§3.3, an index-build span.** Record chunk statistics (C2), extended with embedding statistics (C3).
- **§12, row "2 · C1–C2":** C1 versions by `snapshot_id` and C2 by `params_hash`; the row should name both (C1 `E-C1-9`).
- **§10 `CachedEmbeddings`:** read old cache entries as if they carry the server defaults (1536 dimensions, float, `END`), instead of invalidating them. They were produced with those defaults (C3).

### Hidden review seeds (for the coach; keep them out of lessons, reading files and question files)

- **C1 apply-it tool vs seed S6** (AIQ 04 Q13, "300 PDFs"). The tool implements exactly the signals in that seed's answer. Either use S6 for C1's scored review item before Yash first runs the tool, or swap S6 for a reserve item. Never put the scenario's wording into the tool.
- **C4 MC-005 seed** (book Ch22 vs AE Ch7) and the AIQ Q48/Q50 reserve stay out of the C4 lesson.
- **C7 "Chile" vs "chile" seed** stays out of the C7 lesson. The lesson's value-matching example must use another value; the tool may still check casing in general.

### Errors in 02/03/04/06/08 that span concepts (details in each §4)

- **C1's prerequisite.** 02 and 04 say O2, while 03's edge list says P2 (mastery). P2 is `not_started`, so 03's rule currently blocks C1. Suggested fix: `requires_all: O2` plus `requires_exposure: P2`.
- **The 02 C7 card's failure example does not fail.** "How many customers in Chile?" has 1 matching row, which top-4 already retrieves. The demonstration needs "2021 sign-ups" (43 rows) or the 6 South American rows.
- **06 §3.2 has no row for `embed-v4.0`,** the embedder v0 actually uses.
- **06 §3.1 and the C5 lesson** say temperature 0 makes runs repeatable. Only replay reproduces a run (Foundation §2.7).
- **08 A-05** assumes open-licence documents. Seven of the eight Corpus T candidates carry arXiv's non-exclusive licence, which allows personal study but not redistribution. Only RAPTOR and the Contriever alternative are CC BY.

### What this phase hands to later phases

- **Phase 3 (M1–M5):**
  - The 10 seed items (06 §6.7) are LLM drafts, so they stay out of scored runs until Yash verifies them.
  - The gate needs at least 30 human labels, but 10 seed answers are not enough; M1 supplies the rest.
  - C6's Task 10 open codes seed M5's taxonomy (AE Ch3 method).
  - C2's `--spans` input is the first use of the span-gold format.
- **Phase 4 (I1, I2):**
  - Move 07 Part I, J10 and the Day-14 retrieval practice to the I1 lesson; C2 keeps the mechanism and the units.
  - Structure-aware chunking needs headings, which PyMuPDF's `get_text()` does not give. `pymupdf4llm` or Docling would be I2's inputs.
  - Larger chunk sizes in I1 are not yet proven safe from truncation under Cohere.
- **Phase 5 (R1, R2):**
  - C4's exact-term probe should reuse P3's tokenizer and `bm25_fit_check` settings, so the two stay comparable.
  - R2 can pre-filter with a NumPy mask over `chunks.jsonl`, with no store change.
- **Phase 7–8 (X3, V1–V3):** position effects (MC-004) belong to P7/X3; ALCE citation metrics and any support check belong to M3/V1 under D-10; abstention thresholds belong to V3.
- **Phase 9 (D1–D4):**
  - C6's spans, monitoring page and replay test are D1/D3's first version; D1 extends them rather than rebuilding them.
  - C7's SQL-safety basics link to D4's threat model.
- **Phase 10 (A1):** C7's router overlaps A1's controller-accuracy metric. C7 keeps it minimal and links to A1.

---

## Sources

Every external source used, grouped by the concept that opened it. 'Verified' means the page, file or source code was opened on 2026-10-17 and the fact checked on it; anything else is marked UNVERIFIED. Foundation sources that were reused, not re-opened, are named as such. Course files, book pages and repo cells are listed in each concept's §1.


**C1**

1. [C1-1] Livathinos et al., Docling (AAAI-25 WS), https://arxiv.org/abs/2501.17887 and https://arxiv.org/html/2501.17887 — verified
2. [C1-2] Ouyang et al., OmniDocBench (CVPR 2025), https://arxiv.org/abs/2412.07626 and https://arxiv.org/html/2412.07626v2 — verified
3. [C1-3] Adhikari & Agarwal, PDF parsing tools comparison (preprint), https://arxiv.org/abs/2410.09871 and https://arxiv.org/html/2410.09871v2 — verified
4. [C1-4] PyMuPDF 1.26.7 installed source (`pymupdf.utils.get_text`, flags, `Page.find_tables`, `table.py` L25–26) and https://pymupdf.readthedocs.io/en/latest/page.html — verified
5. [C1-5] pymupdf4llm API, https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html — verified (docs for 1.28.2; 0.2.9 parameters UNVERIFIED)
6. [C1-6] marker README, LICENSE, MODEL_LICENSE, https://github.com/datalab-to/marker — verified
7. [C1-7] unstructured partitioning docs, https://docs.unstructured.io/open-source/core-functionality/partitioning — verified
8. [C1-8] langchain-community v0.4.2 `document_loaders/parsers/pdf.py`, https://raw.githubusercontent.com/langchain-ai/langchain-community/libs/community/v0.4.2/libs/community/langchain_community/document_loaders/parsers/pdf.py — verified
9. [C1-9] pdfplumber README, https://github.com/jsvine/pdfplumber — verified
10. PyPI JSON API (pymupdf, pymupdf4llm, pymupdf-layout, pdfplumber, pdfminer.six, pypdf, unstructured, docling, docling-slim, docling-ibm-models, docling-parse, marker-pdf, langchain-community, langchain-core, langchain-docling, langchain-pymupdf4llm, camelot-py), https://pypi.org/pypi/<name>/json — verified 2026-10-17
11. arXiv abstract pages (licence, version): 2005.11401, 2004.04906, 2212.10496, 2307.03172, 2401.18059, 1810.04805, 1512.03385, 1706.03762, 2112.09118 — verified; PDFs of the first 8 downloaded to the scratchpad and probed (deleted with the scratchpad)
12. Docling model-weight licence; marker/Docling model download sizes; Yash's CPU speed for Docling — UNVERIFIED

**C2**

13. [C2-1] LangChain text-splitters source — https://github.com/langchain-ai/langchain/tree/master/libs/text-splitters/langchain_text_splitters — verified
14. [C2-1] Issue #29884 — https://github.com/langchain-ai/langchain/issues/29884 — verified (open)
15. [C2-1] PR #31222 — https://github.com/langchain-ai/langchain/pull/31222 — verified (closed unmerged)
16. [C2-1] Issue #20908 — https://github.com/langchain-ai/langchain/issues/20908 — verified
17. [C2-2] LlamaIndex `SentenceSplitter` source — https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/node_parser/text/sentence.py — verified
18. [C2-3] Cohere Models — https://docs.cohere.com/docs/models — verified
19. [C2-3] Cohere Embed reference — https://docs.cohere.com/reference/embed — verified
20. [C2-3] Cohere Tokens and tokenizers — https://docs.cohere.com/docs/tokens-and-tokenizers — verified (embed-v4.0 tokenizer UNVERIFIED)
21. [C2-4] Chroma, Evaluating Chunking Strategies for Retrieval — https://www.trychroma.com/research/evaluating-chunking — verified
22. [C2-5] chunking_evaluation — https://github.com/brandonstarxel/chunking_evaluation — verified (page only)
23. [C2-6] NVIDIA, Finding the Best Chunking Strategy — https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/ — verified
24. [C2-7] Bhat et al., arXiv 2505.21700 — https://arxiv.org/abs/2505.21700 — verified
25. [C2-8] Bennani & Moslonka, arXiv 2601.14123 — https://arxiv.org/abs/2601.14123 — verified
26. [C2-9] Pinecone, Chunking Strategies — https://www.pinecone.io/learn/chunking-strategies/ — verified
27. PyPI JSON (langchain-text-splitters, langchain-core 1.6.6, llama-index-core, hypothesis, tiktoken, tokenizers, chonkie, semchunk) — https://pypi.org/pypi/<name>/json — verified 2026-10-17
28. Interview repo (MIT, "Copyright (c) 2026 Om") `04-rag-and-retrieval/questions.md` Q4, Q5; `12-coding-challenges/09_text_chunking.py` — local, verified

**C3**

29. [C3-1] Cohere Embed API v2 reference — https://docs.cohere.com/reference/embed — verified 2026-10-17
30. [C3-2] Cohere Embed models and Models overview — https://docs.cohere.com/docs/cohere-embed, https://docs.cohere.com/docs/models; Embeddings guide https://docs.cohere.com/docs/embeddings — verified; embed price UNVERIFIED (https://cohere.com/pricing shows none); normalisation UNVERIFIED (not stated)
31. [C3-3] Cohere rate limits — https://docs.cohere.com/docs/rate-limits — verified
32. [C3-4] Sentence Transformers, computing embeddings (= Ext C#17, https://sbert.net/) — https://sbert.net/examples/sentence_transformer/applications/computing-embeddings/README.html — verified
33. [C3-5] FAISS wiki, Getting started; MetricType and distances — https://github.com/facebookresearch/faiss/wiki/Getting-started, https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances — verified
34. [C3-6] Chroma docs, collection configuration; embedding functions — https://docs.trychroma.com/docs/collections/configure, https://docs.trychroma.com/docs/embeddings/embedding-functions — verified
35. [C3-7] sqlite-vec docs; vec0 features — https://alexgarcia.xyz/sqlite-vec/, https://alexgarcia.xyz/sqlite-vec/features/vec0.html — verified (exhaustive-vs-ANN UNVERIFIED)
36. [C3-8] Kusupati et al., Matryoshka Representation Learning, 2022 — https://arxiv.org/abs/2205.13147 — abstract verified; venue not checked
37. LangChain `InMemoryVectorStore` source (master) — https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/vectorstores/in_memory.py — verified on master; not checked against the 1.6.6 pin
38. PyPI JSON API — https://pypi.org/pypi/{faiss-cpu,chromadb,lancedb,sqlite-vec,hnswlib,usearch,langchain-core,langchain-community}/json — verified 2026-10-17
39. Cohere Embed 4 launch post — https://cohere.com/blog/embed-4 — opened; contains none of the technical facts (no claim taken from it)
40. LanceDB docs — not opened (UNVERIFIED: default exactness, filters)
41. Local, read-only: cohere 7.2.0 and sentence-transformers 6.1.0 source in `rag_learning/.venv`; HF cache for MiniLM (two snapshots); `uv run python` sqlite3 check

**C4**

42. [C4-1] Karpukhin et al. 2020, DPR — https://arxiv.org/abs/2004.04906 ; https://aclanthology.org/2020.emnlp-main.550.pdf — verified
43. [C4-2] Cohere Embed reference and Embeddings guide — https://docs.cohere.com/reference/embed ; https://docs.cohere.com/docs/embeddings — verified (unit-norm output not stated)
44. [C4-3] BGE-small-en-v1.5 and E5-base-v2 model cards — https://huggingface.co/BAAI/bge-small-en-v1.5 ; https://huggingface.co/intfloat/e5-base-v2 — verified (E5 paper https://arxiv.org/abs/2212.03533 not opened)
45. [C4-4] Liu et al., Lost in the Middle, TACL — https://arxiv.org/abs/2307.03172 — verified (§5, Fig. 11)
46. [C4-5] Cuconasu et al. 2024, The Power of Noise, SIGIR — https://arxiv.org/abs/2401.14887 — verified
47. [C4-6] AIQ 04 Q6 (local, MIT) — https://github.com/ombharatiya/AI-Engineer-Interview-Questions — verified locally @ e080df2
48. [C4-7] OpenInference semantic conventions + LangChain instrumentor — https://github.com/Arize-ai/openinference — verified (main)
49. [C4-8] langchain-core source — https://github.com/langchain-ai/langchain (libs/core) — verified (master)
50. C#18 SBERT semantic-search guide — https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html — UNVERIFIED (not re-opened)

**C5**

51. [C5-1] Groq Reasoning — https://console.groq.com/docs/reasoning — verified 2026-10-17
52. [C5-1] Groq Structured Outputs — https://console.groq.com/docs/structured-outputs — verified 2026-10-17
53. [C5-1] Groq API reference (chat completions) — https://console.groq.com/docs/api-reference — verified 2026-10-17
54. [C5-2] Anthropic Citations — https://platform.claude.com/docs/en/build-with-claude/citations — verified 2026-10-17; plus the `claude-api` skill (ids, prices; cached 2026-10-06)
55. [C5-3] AI-Engineer-Interview-Questions `04-rag-and-retrieval/questions.md` Q28; `03-…/questions.md` Q30; `08-…/questions.md` Q14; `02-…/questions.md` Q44; `12-coding-challenges/08_semantic_search_rag.py` — local pinned copy, verified (MIT, © 2026 Om)
56. [C5-4] Gao, Yen, Yu, Chen (2023), ALCE — https://arxiv.org/abs/2305.14627 and https://arxiv.org/html/2305.14627 — verified (abstract + body to ~100k of 128k chars)
57. [C5-5] Cohere RAG — https://docs.cohere.com/docs/retrieval-augmented-generation-rag ; Cohere RAG citations — https://docs.cohere.com/docs/rag-citations — verified 2026-10-17 (model availability UNVERIFIED)
58. [C5-6] Liu et al. (2023), Lost in the Middle — https://arxiv.org/abs/2307.03172 — verified (abstract only)
59. [C5-7] langchain-community `parsers/pdf.py` (main) — https://raw.githubusercontent.com/langchain-ai/langchain-community/main/libs/community/langchain_community/document_loaders/parsers/pdf.py — verified (main branch, not the repo notebook's pinned version)
60. Foundation sources reused (Groq rate limits/prices, Thinking Machines non-determinism, LangChain defaults) — see LLMOPS_FOUNDATION.md Sources 7, 10, 21, 26

**C6**

61. [C6-1] Lewis et al. 2020, RAG — https://arxiv.org/abs/2005.11401 (PDF v4 read) — verified
62. [C6-2] Barnett et al. 2024, Seven Failure Points — https://arxiv.org/abs/2401.05856 (HTML v1 read) — verified
63. [C6-3] OpenInference semantic conventions — https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md — verified
64. [C6-4] langchain-core `runnables/passthrough.py` — https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/runnables/passthrough.py — verified (the old "return sources" guide at python.langchain.com/v0.2 now redirects; not used)
65. [C6-5] llama-index-core `ingestion/pipeline.py` — https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/ingestion/pipeline.py — verified on `main`; behaviour at the notebook's date UNVERIFIED
66. [C6-6] langchain-community `document_loaders/parsers/pdf.py` — https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/document_loaders/parsers/pdf.py — verified on `main`
67. [C6-7] Husain 2025, A Field Guide to Rapidly Improving AI Products — https://hamel.dev/blog/posts/field-guide/ — verified
68. [C6-8] Gao et al. 2023/2024, RAG for LLMs: A Survey — https://arxiv.org/abs/2312.10997 — abstract only (partly verified)
69. Reused, not re-fetched: Foundation sources 7, 9, 11 (Groq limits, API reference, reasoning), 35 (OpenInference), 37 (OTel GenAI status)

**C7**

70. [C7-1] Sui et al. 2024, Table Meets LLM — https://arxiv.org/abs/2305.13062 — verified (full PDF)
71. [C7-2] Bhandari et al. 2026, Improving Robustness of Tabular Retrieval via Representational Stability — https://arxiv.org/abs/2604.24040 — verified (abstract only)
72. [C7-3] Yu et al. 2018, Spider — https://arxiv.org/abs/1809.08887 — verified (abstract)
73. [C7-4] Li et al. 2023, BIRD — https://arxiv.org/abs/2305.03111 — verified (abstract)
74. [C7-5] Zhong, Yu, Klein 2020, Distilled Test Suites — https://aclanthology.org/2020.emnlp-main.29/ (PDF https://aclanthology.org/2020.emnlp-main.29.pdf) — verified (full PDF)
75. [C7-6] SQLite PRAGMA docs — https://www.sqlite.org/pragma.html; Python sqlite3 docs — https://docs.python.org/3.12/library/sqlite3.html — verified
76. [C7-7] Groq Tool use — https://console.groq.com/docs/tool-use; Structured outputs — https://console.groq.com/docs/structured-outputs — verified (`tool_choice` UNVERIFIED)
77. [C7-8] langchain-community `sql_database.py` — https://raw.githubusercontent.com/langchain-ai/langchain-community/main/libs/community/langchain_community/utilities/sql_database.py — verified
78. PyPI JSON API: https://pypi.org/pypi/duckdb/json, /sqlglot/json, /langchain-community/json, /langchain-core/json, /langgraph/json, /jrag/json — verified 2026-10-17
79. DuckDB `LIKE` case-sensitive / `ILIKE` — UNVERIFIED (not opened)
80. Origin/generator of `customers-100.csv` beyond "dummy data" — UNVERIFIED
81. Nobel Prize API data licence (`json_rag.ipynb` cell 8) — UNVERIFIED
