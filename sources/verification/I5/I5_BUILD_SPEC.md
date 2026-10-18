# I5 build spec: what the lesson, notebook, tool, reading and questions must agree on

**What this is:** the contract for the I5 build (2026-10-18), written before any of the four parts. The HTML lesson, the verify notebook, the apply-it tool, the short reading file and the question file all follow it, so that the same step names, anchors, ids and numbers appear everywhere.
**What this is not:** the lesson. The research behind it is `study/research/phase_04_indexing.md`, Concept I5. The numbers are in [I5_FACTS.md](I5_FACTS.md).

## 0. Ground rules for every part

1. **Numbers come only from `I5_FACTS.md`** (and its source `out_i5_kit_measure.txt`). Label each one measured / toy / formula / external, and DERIVED token estimates as estimates. Never invent a number, a page or a citation.
2. **MiniLM was not available in the build session** (`huggingface.co` blocked). Nothing may claim a MiniLM margin, rank or exact WordPiece count for the header arms. The notebook and the tool compute them when the model is in the local Hugging Face cache, and SKIP (with a printed reason) otherwise. The lesson shows them as "your run" placeholders.
3. **Book (Ch7, 11 pages) not present in the build session.** Pages are cited as 02/04 give them: Ch7 p.1–2/11 (the problem), p.4/11 (document title), p.4–7/11 (steps), p.7/11 (embed and store), p.8/11 (richer headers; reuse for reranking and generation), p.8–9/11 (the 0.1 → 0.9 claim, unmeasured). Checks that need the book (page exists, phrase on page, 15-word copyright) run when the book folder exists and SKIP otherwise.
4. **No API call anywhere.** No Groq, Cohere, Claude; no `.env` read; no network.
5. **Hidden seeds:** never use anything from `sources/coach/transfer_seed_bank.md`. Coach-banned phrases (must not appear in the reading or question file): `share of queries`, `fraction of queries`, `a guide says`, `sixth`, `add a pdf`, `adding a document`, `new document`, `another pdf`, `tenant`, `300 pdf`, `without reading`, `half noise`, `0.729`, `three stages`.
6. **House style:** `curriculum/WRITING_STYLE.md` and `study/PORTABLE_LESSON_STYLE.md` B3. Plain English, short sentences, "you", the answer first, one running example, the tempting wrong idea vs the right one, honest limits. Never copy 15 or more consecutive words from any source; MIT text may be quoted with its notice.
7. **Default paths** (as P2/P4): the workspace is `rag_learning/` (= the repo root); the upstream repo is `<workspace>/../upstream/RAG_Techniques`, the interview repo `<workspace>/../upstream/AI-Engineer-Interview-Questions`, the book `<workspace>/../RAG_Made_Simple_The_Complete_Visual_Guide`. Scripts take the "Book RAG" folder (the workspace's parent) as an optional argument.

## 1. Files

| Part | Path |
|---|---|
| Facts | `sources/verification/I5/I5_FACTS.md`, `i5_kit_measure.py`, `out_i5_kit_measure.txt` |
| HTML lesson | `study/lessons/I5_contextual_headers.html` (the P2 shell, unchanged CSS and shared script) |
| Gap audit | `study/lessons/I5_contextual_headers_gap_audit.md` |
| Verify notebook | `study/notebooks/I5_headers_verify.ipynb`, built by `sources/verification/I5/i5_build_verify_nb.py`, run by `i5_verify_nb_run.py` → `out_i5_verify_nb_run.txt` |
| Apply-it tool | `study/tools/header_fit_check.py`; tests `sources/verification/I5/i5_tool_test.py` → `out_i5_tool_test.txt`; example report `study/tools/examples/climate_header_report.md`; toy LLM contexts `study/tools/examples/climate_contexts_toy.jsonl` |
| Reading file | `study/reading/I5_contextual_headers.md` |
| Question file | `study/questions/I5_questions.md` |
| Markdown check | `sources/verification/I5/i5_md_check.py` → `out_i5_md_check.txt` |
| Kit wiring | `study/kit.py` `_TOOL_HINT["I5"] = "header_fit"` |

## 2. The running example

Corpus D (the climate PDF), v0's 97 chunks (07 recursive chunker, per page, 1000/200; `params_hash 1ca9c5a3b548`), and two draft seeds that are near-duplicates of each other:
- **D-002** "In what year was the Paris Agreement adopted?" Gold chunk **27** (p.10). Distractor pages 6, 23, 24.
- **D-003** the NDC "regular reviews and updates" question. Gold chunk **68** (p.23). Distractor pages 6, 10.

The two "Paris Agreement" headings: p.10 under Chapter 6 › International Collaboration; p.23 under Chapter 16 › International Agreements. Only the chapter and section levels separate them.

Header arms (the `embed_text = header + "\n\n" + text` template; `text` never changes):

| Arm id | Header | Distinct / 97 |
|---|---|---|
| `none` | — | 1 |
| `title` | `Understanding Climate Change` | 1 |
| `path` | title › chapter › section › subsection in effect at the chunk's first non-space character (**start rule**) | 97 |
| `major` | the path that covers most non-space characters of the chunk (**majority rule**) — the lesson's recommended default | 96 |

Path separator: ` › ` (U+203A with spaces).

## 3. Steps, anchors and headings (identical in lesson, reading and notebook)

| Step | HTML id | Reading heading (exact) | Teaches | Key numbers (I5_FACTS) |
|---|---|---|---|---|
| 1 | `anon` | `## 1. A chunk loses its context` | contextual anonymity: pronouns, orphaned heading, chapter; Corpus D reality | 0 chunks without a heading; 31 orphaned-heading chunks (16 at a page end, = 07 D.8); 46 start mid-sentence; chunk 34 starts with "It" |
| 2 | `fields` | `## 2. Where the header goes: embed_text, not text` | `embed_text` vs `text`; span invariant; three inputs (embedding v1.2, BM25 v2.0, generation later); `preproc_version` → `embed_hash`; queries unchanged | invariant holds for 97; separator `\n\n` |
| 3 | `tree` | `## 3. Get the headings from the PDF` | font size + bold from `get_text("dict")`; metadata title empty; body-size bold subsections | 814/192/68/22/1 lines; 1/21/68/192 headings; 0.68; 1–9–11 per page; one every 257 chars |
| 4 | `path` | `## 4. The path, not the leaf` | leaf collisions; path separates at chapter level | 11 reused names; the two Paris paths; path 75/120/168 chars ≈ 12/19/27 tokens (DERIVED) |
| 5 | `assign` | `## 5. Which heading a chunk gets` | start vs majority vs all-inside rules | 94 of 97 hold ≥ 2 headings; 84 of 97 start ≠ majority; chunk 27 (start = Chapter 6 only); chunk 68 (start = Chapter 15, majority = Chapter 16 › … › Paris Agreement); all-inside 93/198/306 chars |
| 6 | `info` | `## 6. The information test: a constant title adds nothing` | a header discriminates only if it varies; distinct headers / chunks; constant prefix still shifts vectors; BM25 floor | title 1/97; path 97, majority 96; idf floor 0.8565 for understanding/climate/change (df 97) |
| 7 | `dilute` | `## 7. Dilution and the header magnet` | mean pooling share `s = h/(h+c)`; shared headers pull chunks together | s 0.106 / 0.112 / 0.229; char share 0.029/0.119/0.201; toy K13 table |
| 8 | `trunc` | `## 8. Truncation: the tail is cut` | `h + c > 256` cuts the chunk's tail, not the header; specials inside the 256 | 182 + 27 = 209 fits; 182 + 100 = 282 over by 26; about 29 of 97 with a 100-token context (DERIVED); 0 for path headers |
| 9 | `measure` | `## 9. Measuring it on your questions` | CE@4 on dev at fixed k; per category with n; discordant pairs; distractor margin; leakage check; ceiling; detectable effect | BM25 preview 8/8, 8/8, 0.938 in every arm (ceiling); K8 no leaked word; 06 §9.4: ±0.124, ~0.18 |
| 10 | `llm` | `## 10. LLM-written contexts and the cost ladder` | Anthropic's method (whole doc + chunk → 50–100 tokens); dsRAG's document-level header; ladder rungs 0–3; Groq per-request limit | rung 2 $0.0124, median 855 tokens/call, 106,743 tokens, ≥ 13.3 min; rung 3 13,090 tokens/call > 8,000 TPM; 1,269,730 vs 200K TPD |
| 11 | `cache` | `## 11. Prompt caching, cache keys and wrong contexts` | prefix caching (doc first, chunk last; process in document order); write/read multipliers; minimum prefix (silent no-cache); cache key = prompt version + document + chunk; entity-in-document check | Haiku 5.5 uncached $0.1367 vs cached $0.0261 (5.2×); K12: 96 of 97 stale vs 0 of 97; cookbook 3,412 tokens < 4,096 on Haiku 4.5 |
| 12 | `claims` | `## 12. Reading the vendor numbers` | 1 − recall@20 vs CE@4; absolute vs relative; upstream 0.106 → 0.922 is a reranker score on one Nike chunk whose query names "Nike" | −2.0 points / −35.1%; −49.1%; −66.7%; Pass@10 87.15 → 92.34 → 95.26; KITE 4.72 → 6.04 |
| 13 (Full) | `repo` | — | upstream notebook read critically (cells 8, 9, 11, 13, 15) | K14 |
| 14 (Full) | `beyond` | — | late chunking; LlamaIndex metadata defaults; dsRAG section summaries; contextual BM25 preview; hosted contextual embedders | external |
| — | `verify`, `apply`, `check` | `## 13. When not to use it`, `## Check yourself` (reading only) | | |

GitHub anchors of the reading headings: `#1-a-chunk-loses-its-context`, `#2-where-the-header-goes-embed_text-not-text`, `#3-get-the-headings-from-the-pdf`, `#4-the-path-not-the-leaf`, `#5-which-heading-a-chunk-gets`, `#6-the-information-test-a-constant-title-adds-nothing`, `#7-dilution-and-the-header-magnet`, `#8-truncation-the-tail-is-cut`, `#9-measuring-it-on-your-questions`, `#10-llm-written-contexts-and-the-cost-ladder`, `#11-prompt-caching-cache-keys-and-wrong-contexts`, `#12-reading-the-vendor-numbers`, `#13-when-not-to-use-it`.

Lesson links from the question file use `../lessons/I5_contextual_headers.html#<id>`.

## 4. Question file: ids, sets, what each tests, where it is taught

`<!-- kit:questions concept=I5 version=1 -->`, title `# I5 questions: contextual chunk headers and contextual retrieval`.

| id | type | set | Tests | Reread |
|---|---|---|---|---|
| I5-PRE-01 | R | pre | why a chunk like "It was adopted in 2015 …" can miss a question that names its subject | §1 |
| I5-PRE-02 | R | pre | does prepending the one document title to every chunk help ranking? (cold guess) | §6 |
| I5-R-01 | R | main | "contextually anonymous"; the two kinds of context a header restores (where it sits: heading path/chapter; what it refers to: the subject of "it/this") | §1 |
| I5-R-02 | R | main | one-document corpus: why a title header adds no discriminating information, and what it still changes (shifts every vector; BM25 floor) | §6 |
| I5-R-03 | R | main | the three inputs (embedding, BM25, generation); v1.2 changes the embedding input only | §2 |
| I5-R-04 | R | main | why the header lives in a separate field (`embed_text`), not in `text` (span invariant, CE scoring, `preproc_version`) | §2 |
| I5-R-05 | R | main | what Anthropic's "35%" measures (relative drop in 1 − recall@20, 5.7 → 3.7) | §12 |
| I5-R-06 | R | main | why prompt caching makes the whole-document arm cheap, and what makes a cache silently miss (prefix below the minimum; changing prefix; order) | §11 |
| I5-A-01 | A | main | 182-token chunk + 27-token path header; + 100-token LLM context: which text is truncated, where | §8 |
| I5-A-02 | A | main | cost of the whole-document arm on D with Haiku 5.5, with and without caching (data given in the question) | §10, §11 |
| I5-A-03 | A | main | write the p.10 and p.23 "Paris Agreement" path headers; which level separates them | §4 |
| I5-A-04 | A | main | 5.7% → 3.7% as absolute and relative change; detectable on 50 questions (06 §9.4)? | §12, §9 |
| I5-A-05 | A | main | chunk 68: the header under the start rule and under the majority rule; which is right for D-003 and why | §5 |
| I5-A-06 | A | review | header share s for a 19-token header on a 151-token vs a 64-token chunk | §7 |
| I5-T-01 | T | main | headers raised CE@4 on near-duplicate items but lowered it on factual-single-span items: what to check first | §7, §9 |
| I5-T-02 | T | main | after a one-line edit on page 12, contexts for the other chunks came back from cache unchanged: what was wrong with the key | §11 |
| I5-T-03 | T | main | first Groq whole-document call fails with "request too large / TPM": why, and two fixes | §10 |
| I5-T-04 | T | main | a teammate wrote questions by reading section titles, and headers gave +20 points: what is suspicious, how to check | §9 |
| I5-R-07 | R | interview | AIQ 04 Q17 (`source=AIQ-04-Q17`), verbatim, MIT notice; repo answer quoted first; our check adds: on a one-document corpus the title part of "title + heading path" is constant (K5), so "unconditionally" needs the information test; and the heading rule matters (K4) | §1, §6, §10 |

Only one external item (I5-R-07). FORMAT rules apply in full (hints 1 and 2; Hint 3 only on A items; 2–5 key points; 1–2 "for a 4"; 1–3 common wrong answers; one short question sentence, data after it; reread names a reading section, the lesson step, and a book page `Ch7 p.x/11`).

The interview item's question field: `"Explain contextual retrieval. What problem does it solve, and how does late chunking relate?"` then the notice line `*From ombharatiya/AI-Engineer-Interview-Questions @ e080df2, \`04-rag-and-retrieval/questions.md\` (question 17), Copyright (c) 2026 Om, MIT License.*` Quoted repo paragraphs must be exact substrings of the pinned file.

## 5. Reading file

`<!-- kit:reading concept=I5 depth=short version=1 -->`, `# I5: Contextual chunk headers and contextual retrieval`. What this is / is not. Book box: `> **Read in the book:** Ch7 p.1–2/11, then p.4–9/11. Read after §2.` Sections exactly as §3 above (1–12, then 13 When not to use it, Check yourself → `study/questions/I5_questions.md`). 1,800–3,000 words of prose (code blocks excluded). Every key point of every question in §4 must be answerable from it.

## 6. Verify notebook

Sections numbered like the lesson steps 1–12. Expected values from I5_FACTS; same code paths as `i5_kit_measure.py`. A `check(name, got, expected)` helper prints PASS/FAIL; `skip(name, reason)` prints SKIPPED. The final cell prints `N checks passed / M failed / S skipped`. MiniLM section (step 8 exact tokens; step 9 margins and CE@4 per arm; Kendall τ) runs only if the model is cached; otherwise SKIPPED with the reason. Plotly charts: heading strip (33 pages × levels, reused names marked), path-rule disagreement, header length by rule, dilution curve with the toy (K13), truncation bars, cost ladder bars, BM25 preview table, margins dumbbell (MiniLM, skipped here). No API call; offline.

## 7. Apply-it tool: `header_fit_check.py`

"Would contextual headers help my documents, and which kind?" Inputs `--docs` (PDF/txt/md, files or folders), `--questions` (06 spans JSONL like `study/tools/examples/climate_seed_spans.jsonl`, or `{"q", "expect"}` JSONL), `--rule start|majority|all` (default majority), `--chunk-size 1000 --overlap 200` (v0 chunker, per page; must reproduce the 97 chunks), `--limit 256`, `--embedder none|minilm` (default none), `--contexts contexts.jsonl` (`{"chunk_id" or "seq", "context"}`), `--report out.md`, `--jsonl log.jsonl`. Checklist H1–H12 (research §8) with ✓ / ✗ / ? and evidence; recommendation rules in research §8 order (first match wins). Token counts: the MiniLM tokenizer when cached, else characters ÷ 6.21 marked "estimate". No API, no network. The example report on the climate PDF with the 10 draft seeds must reproduce I5_FACTS K2–K9.

## 8. Checks before delivery

- Facts: `i5_kit_measure.py` twice, byte-identical.
- Notebook: runner exits 0 (all non-skipped checks pass, no cell error).
- Tool: `i5_tool_test.py` all pass; example report regenerates byte-identically.
- Markdown: `i5_md_check.py` all pass (or SKIPPED only for book-dependent checks, with the reason); `uv run python study/quiz.py --check` OK.
- Lesson: browser tests (Short/Full, 7 themes × light/dark, panel left/right/hidden, T key, ↑ button, every interactive part and quick check, 390 px without sideways scroll, no console errors, works from file:// and through the kit server).
