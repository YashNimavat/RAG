# I-CMP build spec (2026-10-18): the granularity-family lesson, in the P1/P2 format

**What this is:** the one shared plan for every I-CMP study-kit file, written before any of them, so the HTML lesson, the reading file, the question file, the verify notebook and the apply-it tool use the same steps, ids, numbers and words. Helpers build from this file; the lead checks every file against it.
**What this is not:** the research (that is `study/research/phase_04_indexing.md`, "Concept I-CMP") or the facts (that is `I-CMP_FACTS.md` in this folder). Where this spec and the facts disagree, the facts win; report the disagreement.

## 0. Ground rules (all files)

1. **Numbers.** Every number comes from `I-CMP_FACTS.md` (K1–K12, §2, §3) or is arithmetic shown on the page. Label each one **measured** (from `out_icmp_kit_measure.txt`), **toy** (made-up), **formula** (computed), **derived** (cost arithmetic from measured counts) or **external** (a cited study, from the research's §5.2). Never invent a number, page or result.
2. **The draft seeds are not labels.** The 8 answerable seeds are `llm-draft`. Every rank, CE value or Δ on them is "an observation on 8 draft seeds, not a result". They saturate v0 (CE@4 8/8), so they cannot show an arm beating v0.
3. **No I1–I6 run exists.** The comparison table's honest state for every real arm is "not run" (with the reason) or "derived" (cost only). The buildable arms in K4–K7 are **probes**: v0, three I1 grid points, pages, uncapped sections, and an "I3 probe" (MiniLM, our regex splitter, p90, no cap). Never call a probe "the I2 arm" or "the I3 result".
4. **Book.** The book was not opened in this session. Cite book pages only as listed in §6 below, always marked as page pointers (no claims beyond the research's own paraphrase). No book text, no quotation. App A ratings are "the book's rating (no scale)" and sit in their own column, never beside a measurement.
5. **Repo (custom non-commercial licence).** Paraphrase; quote at most short identifiers or settings (`breakpoint_threshold_amount=90`). Cells are 0-based.
6. **Interview repo (MIT, © 2026 Om).** Only AIQ `04-rag-and-retrieval/questions.md` Q4 @ e080df2, quoted with its notice: in the interview item, and the lesson may credit its "Handbook > Benefits > Parental leave" example.
7. **Hidden seeds (CR-13): banned.** Never write, adapt or hint at: the vendor-number critique (a vendor's 1 − recall@20 / 5.7% vs our CE@4: a P6 reserve); the "two sources disagree about k" scenario (C4 seed S7); a whole-document manual (S1); an added document changing scores (S2); stage reliability multiplication (S8). **So Anthropic's Contextual Retrieval row is left out of every I-CMP file**, including the metric-translation table. Banned phrases (checked by `icmp_md_check.py` and the lesson test, case-insensitive): `a guide says`, `who is right`, `5.7%`, `recall@20`, `top-20`, `top 20`, `anthropic`, `share of queries`, `fraction of queries`, `sixth`, `add a pdf`, `adding a document`, `three stages`, `25,000-token`, `chile`.
8. **Style.** `visual-learning-writer/references/WRITING_STYLE.md` and `study/PORTABLE_LESSON_STYLE.md` B3: answer first, plain words before terms, one running example, "Common mistake" and "In your project" per step, short sentences, "you". British spelling as in P1/P2 (normalise, labelled).
9. **Ids and names.** Concept id `I-CMP`. Files: `study/lessons/I-CMP_granularity.html`, `study/lessons/I-CMP_granularity_gap_audit.md`, `study/reading/I-CMP_granularity.md`, `study/questions/I-CMP_questions.md`, `study/notebooks/I-CMP_granularity_verify.ipynb`, `study/tools/chunker_chooser.py` (+ `study/tools/examples/`), checks in `sources/verification/I-CMP/`. Previous topic I6, next topic R1 (Phase 5). In kit routes: `#/c/I-CMP`, `#/c/I6`, `#/c/R1`.
10. **Running this container's checks.** Hugging Face and the tiktoken host are blocked here, so every run sets
    `HF_HOME=/tmp/claude-0/-home-user-RAG/9f4a7f6d-e19b-5e8f-bf21-36c434a177a7/scratchpad/hf`,
    `TIKTOKEN_CACHE_DIR=/tmp/claude-0/-home-user-RAG/9f4a7f6d-e19b-5e8f-bf21-36c434a177a7/scratchpad/tiktoken_cache`,
    `HF_HUB_OFFLINE=1`, `PYTHONIOENCODING=utf-8`, and uses `.venv/bin/python` from `/home/user/RAG`. The upstream repo and the AIQ repo are at `/home/user/upstream/RAG_Techniques` and `/home/user/upstream/AI-Engineer-Interview-Questions` (= `WS.parent / "upstream" / …`, the same layout as the learner's machine). Never hard-code the scratchpad path inside a deliverable; it only goes into the environment of a command.

## 1. The answer first (5 sentences; lesson, reading §0 summary)

Every member of the granularity family changes one of two things: **where the boundaries go** (fixed windows, document structure, embedding-distance breakpoints, LLM-written propositions) or **what text stands for a unit in the index** (a header, generated questions); a third choice, **retrieving a small unit but returning its parent**, cuts across both. They differ in size unit, size spread, index-time cost (from 0 LLM calls to about one per proposition), index size, and the failure they target. None is better in general. A fair comparison holds the questions, labels, embedder and **token budget** fixed, and with 12–16 dev questions most differences will honestly read "inconclusive". So for a new corpus you match its structure and question mix to each member's target failure and cost, pre-register at most three arms, and write "not run" or "not comparable" wherever you have no fair number.

## 2. The theory in one read (11 ideas, each links to its step)

| # | Idea | Formula / rule | Step |
|---|---|---|---|
| 1 | Two axes plus one | unit = boundary(text); pointer = representation(unit); returned = parent(unit) or the unit | 2 |
| 2 | Units | chars ≈ tokens × ρ, ρ measured per corpus and tokenizer (D: WordPiece 6.21, cl100k 5.57, o200k 5.65, gpt2 5.05) | 3 |
| 3 | Size distribution | report min / median / p95 / max; truncation share = #(tokens > L) / N, L = 256 for MiniLM | 4 |
| 4 | Index-time cost | E (embeds), L (LLM calls), T (input tokens) per member (table in §4 below) | 5 |
| 5 | Query-time cost and index size | 1 query embed, 0 LLM calls for every member; bytes = 128 + N_vectors × d × 4 | 5 |
| 6 | Equal budget | walk the ranked list while Σ tokens ≤ B (`take_within_budget`); dedup parents first; B ≥ the largest unit | 6 |
| 7 | Fair comparison | identical comparison keys; one variable; fixed k **and** equal B | 6, 7 |
| 8 | Honest cells | measured · inconclusive · not run (reason) · not comparable (which key) · derived · book rating (own column) | 7 |
| 9 | Target failure | each member is a hypothesis about one M5 bucket; "when not to use" is part of the row | 8 |
| 10 | Conditional effects and family error | Δ(arm \| champion) ≠ Δ(arm \| v0); FWER = 1 − (1 − α)^m; Holm; MDE ≈ 2.8·√(b + c)/n | 9 |
| 11 | Choosing | priority = bucket count × severity / cost; other people's numbers transfer as directions and design rules, not values | 10, 11 |

## 3. Lesson steps (HTML section ids are fixed; the reading file has one `## N.` section per step, same order)

| Step | id | Heading idea (reading-file heading) | Main facts | Visual (lesson) |
|---|---|---|---|---|
| 1 | `upstream` | Seven notebooks, seven setups ("1. Seven notebooks are not a comparison") | §2 table: 4 corpora, 5 size units, 6 embedder settings, 5 LLM ids, k 1–5 | the units table, rows highlight what differs |
| 2 | `axes` | Two axes and a return arrow ("2. Two axes and a return arrow") | I1–I6 placed: boundary (fixed I1, structure I2, semantic I3, proposition I4), representation (header I5, generated questions I6), return (I6 parent, I4 → source chunk, X1 window later) | 2-axis SVG map; toggle "show returned unit" |
| 3 | `units` | Units first ("3. Name the unit before the number") | K2 ρ table; "1,000 tokens" ≈ 5,570 cl100k characters vs v0's 1,000-character chunk (149 WordPiece median); regex words 9,406; sentences 612 | unit converter: type a size and a unit, see the other units (uses K2 ρ) |
| 4 | `sizes` | Size spreads and the cap ("4. Look at the spread, not the mean") | K4 for the 7 probes; truncation shares 0 / 0 / 6.2% / 49.2% / 97.0% / 1.1% / 29.0%; I3 probe max 4,029 chars, 686 tokens; sections min 30 chars | strip plot of WordPiece tokens per arm with the 128 and 256 lines (hand-drawn SVG; per-arm points from embedded arrays) |
| 5 | `cost` | What each member costs ("5. Index-time cost, query-time cost, index size") | K10 ladder; K11 crossover; bytes; I5 per-chunk 13,280-token request > 8,000 TPM | cost ladder bars, log scale (LLM calls and input tokens); crossover calculator (Q_total, rebuilds) |
| 6 | `budget` | Equal k or equal budget ("6. Compare at the same token budget") | K6: B = 671; 500/100 7/8 → 8/8; 1500/300 7/8 → 5/8; pages 5/8 with 1,590 tokens → 2/8 at k = 1; I3 probe k = 0 for D-001 (769 > 671); K12 toy dedup | paired bars per arm: CE at k = 4 vs at B, with context tokens; dedup toy toggle |
| 7 | `cells` | Filling the table honestly ("7. What a cell may say") | legend; the comparison table template with states; K8 refused subset; 06 roll-up is missing columns (research I-CMP-E5) | the comparison table with cell-state chips; legend |
| 8 | `targets` | Which failure each member targets ("8. Each member is a hypothesis about one failure") | M5 buckets; "when not to use" per member; K5 title header 1 of 97 distinct, path 71 of 97, share 0.103; K3 11 repeated heading names, 68% bold-only headings | heat table template: members × buckets, arrows = hypothesis, cells "not run" |
| 9 | `family` | Many arms, few questions ("9. Many arms, few questions") | lineage (conditional effects); K9 FWER 0.2262 / 0.4596; Holm 0.0167 / 0.025 / 0.05 and the toy; MDE 0.4667 at n = 12; K7 seeds: c = 0 everywhere, page 3–0 p 0.25, bootstrap overconfident at n = 8 | FWER curve over m; MDE calculator (n, b + c); lineage graph v0 → v1.0 → v1.1 → v1.2 → v1.3 → v1.4 with "not run yet" |
| 10 | `others` | Other people's numbers ("10. Other people's benchmarks") | metric-translation table WITHOUT the Anthropic row: Chroma (char-range recall/IoU at k = 5; bigger chunks raise recall and lower IoU at fixed k), Qu, Tu & Bao (F1@5; semantic wins on stitched data, fixed-size on real), NVIDIA (page-level strong on paginated PDFs; metric scale unstated), HiChunk (answer metrics at a fixed 4,096-token context), Merola & Singh (contextual vs late chunking: cost vs coherence); KITE repo claim; what transfers: directions under conditions and design rules (span gold, equal budget, evidence-dense items) | the translation table |
| 11 | `choose` | Choosing for a new corpus ("11. Choosing for a corpus you have not seen") | decision flow (K3 structure? K4 near-duplicates? K5 anonymous? K6 question mix? K7 cost per rebuild?); worked example: an HR policy handbook, 120 Markdown pages with clean H1–H3, three near-identical regional versions (UK/US/IN), questions like "parental leave in region X", updated monthly → A0 recursive 1000/200, A1 = I2, A2 = I2 + I5 (region + title + section path, 0 calls); skip I3, I4; I6 only if a vocabulary-mismatch bucket appears; CE@4 primary at fixed k and equal B, guards MRR@10 and context tokens, Holm over 2 comparisons, dev → one test touch. Credit AIQ Q4's heading-path example (MIT, © 2026 Om). Never use Corpus H | flowchart; the plan as a card |
| 12 | `project` | For your project ("12. What this means for v1.x") | the roll-up columns to add (index calls, tokens, bytes, base champion, k and B, split and n, qid-set hash, "comparable to"); the family register; decisions move to Corpus T, D for parity (06 §5.1); grow dev before v1.0 (research decision 1) | table |
| 13 (Full) | `repo` | The repo, read critically | HyPE cell 11 SyntaxError, 97/97 saved output, `set()` dedup at k = 3; `choose_chunk_size` loads every file in `../data` and sets the judge after generating questions (I-CMP-E10, UNVERIFIED folder contents); proposition notebook grades with the same model that generates; semantic notebook has no size cap; CCH builds no index | table |
| 14 (Full) | `book` | The book, checked | App A Low/Medium/High ratings with no scale (UNVERIFIED pages); the strategy spectrum lists the context window as a chunker although it is not (DV-B12; X1); Ch8 page disagreement (I-CMP-E1) | table |
| 15 (Full) | `beyond` | Beyond the family | late chunking (needs a long-context embedder with token outputs); HiChunk auto-merge; Chroma's precision Ω and the precision denominator that sums overlapping chunks; the I6 vs Q2 crossover with caching; Corpus T vs D disagreement as a finding | text |

Practise and apply: `verify` (notebook), `apply` (tool + checklist), `check` (3 quick questions + quiz link). Footer: sources and status.

## 4. The cost table (lesson step 5, reading §5, question I-CMP-A-02 uses the formulas)

| Member | Index-time LLM calls | Embeds | Vectors | D value (K10) |
|---|---|---|---|---|
| I1 fixed / recursive, I2 structure | 0 | N | N | 97 calls 0 |
| I3 semantic | 0 | S + N (sentence windows for breakpoints, then chunks) | N_sem | S = 612 → 709 embeds, 9 Cohere calls |
| I4 propositions | N_base (generate) + P (grade per proposition) | P | P | ASSUMPTION ≈ 96 + 960 = 1,056 calls |
| I5 deterministic header | 0 | N | N | 0 calls, 97 embeds |
| I5 per-chunk context | N, each with the whole document | N | N | 97 calls, ≈ 1.29M input tokens, ≈ $0.10–0.13; one request ≈ 13,280 tokens |
| I6a document-level questions | D_windows | fragments + questions | fragments + questions | 3 calls, 204 vectors |
| I6b HyPE | N | N × q | N × q (original vector dropped) | 97 calls; q = 8 → 776 vectors |

## 5. Question file `study/questions/I-CMP_questions.md` (17 items)

Header: `<!-- kit:questions concept=I-CMP version=1 -->`, title `# I-CMP questions: the granularity family, compared fairly`. Ids `I-CMP-<type>-<nn>`. Every reread line links to the reading file **and** the lesson anchor (`../lessons/I-CMP_granularity.html#<id>`), plus a book page from §6 where one fits (else "book: none for this point").

| id | set | type | Steps | Asks (scenario must be ours; data inside the Question) |
|---|---|---|---|---|
| I-CMP-PRE-01 | pre | R | 3 | Two chunkers both say "size 500". Can you compare their results directly? (units) |
| I-CMP-R-01 | main | R | 2 | Name the two axes and the third choice; place I1–I6 |
| I-CMP-R-02 | main | R | 6 | Why hold the token budget equal as well as k? |
| I-CMP-R-03 | main | R | 7 | What may a cell say instead of a number, and when? |
| I-CMP-R-04 | main | R | 9 | Why is each v1.x effect conditional, and what must every row record? |
| I-CMP-R-05 | main | R | 8 | Why can Corpus D not test a document-title header? (1 distinct of 97; path 71 of 97) |
| I-CMP-A-01 | main | A | 6 | Equal-budget k: a ranked list for three arms with token counts and B = 600 (our numbers; one HyPE-style arm with duplicate parents); give k, tokens used and distinct units for each, with `break` |
| I-CMP-A-02 | main | A | 5 | Index-time cost on a 100-chunk corpus: 600 sentences, a 8,000-token document, 150 tokens per chunk, 10 propositions per base chunk (90 base chunks), 5 questions per chunk, 3 document windows: LLM calls, embeds and vectors for I3, I4, I5 per-chunk (with input tokens, 100 instruction tokens), I6b |
| I-CMP-A-03 | main | A | 9 | Five rounds each confirm one arm on test at α 0.05, no true effect: chance of ≥ 1 false adoption (0.2262); then Holm on three given p-values 0.004, 0.030, 0.020 (sorted against 0.0167 / 0.025 / 0.05, Holm rejects all three; Bonferroni at 0.0167 rejects only 0.004) |
| I-CMP-A-04 | main | A | 9 | Dev has 12 answerable items; discordant b + c = 4: smallest detectable CE@4 difference (≈ 0.47); and what one item is worth (0.083) |
| I-CMP-A-05 | main | A | 4 | Given 10 chunk token counts for an uncapped arm (ours), compute the truncation share at 256 and say what the embedder misses |
| I-CMP-A-06 | review | A | 3 | Convert "chunk_size 1,000 tokens (cl100k)" to characters on a corpus with ρ = 5.57, and compare with v0's 1,000-character chunk (≈ 5.6× larger) |
| I-CMP-T-01 | main | T | 11 | Choose arms for an unseen corpus: a support knowledge base of 2,000 short FAQ articles (150–400 words), each with a title and no sub-headings, customers ask in their own words, re-indexed nightly (only changed articles); write the pre-registered plan (≤ 3 arms, primary metric, k and B, Holm, dev/test). Expected: articles as units / I2 at article level; I5 title header (titles differ across documents, unlike Corpus D); consider I6b for paraphrase mismatch only with a content-keyed cache so nightly runs re-pay only changed articles; skip I3 (short articles), I4 (cost, lookup questions) |
| I-CMP-T-02 | main | T | 10 | One report ranks chunker A first on character-range recall at k = 5, another ranks chunker B first on IoU on the same data: how can both be true, and what would you measure instead? |
| I-CMP-T-03 | main | T | 7 | v1.4 ran on a 5-page subset with 14 of the dev qids. Can its CE@4 sit beside v1.3's in the roll-up? (No: rerun the champion on those qids; "not comparable: qids") |
| I-CMP-T-04 | review | T | 9 | On 8 draft seeds the page arm loses 3–0 to v0 at k = 4 and a bootstrap CI excludes 0. Do you record "pages are worse"? (No: draft labels; exact McNemar p 0.25; Holm across arms; at most "observation"; and pages used 2.4× the tokens) |
| I-CMP-R-06 | interview | R | 2, 6, 10, 11 | AIQ 04 Q4 verbatim ("What chunking strategies do you know, and how do you pick one?") with the follow-up "How do you A/B test two chunking strategies?" (source=AIQ-04-Q4). Preamble: the repo's answer quoted (≤ 3 short paragraphs, verbatim, with notice), then "Our check of that answer": mostly sound; (1) "gains marginal" for semantic chunking is an opinion consistent with Qu, Tu & Bao, who found semantic wins on stitched data; (2) "structure-aware whenever structure exists" depends on detecting it: on Corpus D 68% of headings are bold body-size text that a size-only detector misses; (3) the A/B answer it does not give: identical comparison keys, span gold, fixed k and equal budget, paired test, MDE at your n, pre-registered arms |

Rules: FORMAT.md §2 (2–5 key points, 1–2 "for a 4", 1–3 common wrong answers, Hint 1 and 2 required, Hint 3 only on A items); one short question sentence (≤ 45 words) before any data; at most 2 external items (here only R-06). The numbers in A items are toy numbers written for the item and must be recomputed by `icmp_md_check.py`.

## 6. Book pointers allowed (all UNVERIFIED in this session)

Ch9 p.10–11/14 (where semantic chunking sits; the strategy spectrum) · Ch4 p.10–11/15 (propositions vs standard chunks) · Ch8 p.7–10/11 (comparisons; the two plans disagree on the exact page) · App p.9–11/23 (quick-reference cost tables, decision tree; no scale) · Ch1 p.10–11/14 (chunk-size trade-off) · Ch11 p.9–10/13 (HyPE as the mirror image of HyDE) · Ch7 p.8/11 (richer headers). The reading file's book box: "Ch1 p.10–11/14 before §3; Ch9 p.10–11/14 and Ch4 p.10–11/15 before §2; Ch11 p.9–10/13 before §5; App p.9–11/23 before §8 (read its ratings as hypotheses)". Write pages exactly as `ChN p.x/y` / `App p.x/y`.

## 7. Reading file `study/reading/I-CMP_granularity.md`

FORMAT §3 shape: `<!-- kit:reading concept=I-CMP depth=short version=1 -->`, `# I-CMP: The granularity family, compared fairly`, What this is / is not, the book box (§6), a provenance paragraph (facts file, draft seeds, no API call), `## 1.` … `## 12.` with the headings of §3 above (in quotes there), `## 13. When not to use it` (when NOT to run a bake-off: one corpus that already works at the gate; no labels yet; only one cheap arm worth trying), `## Check yourself` → `study/questions/I-CMP_questions.md`. 1,800–3,000 words of prose (code blocks excluded). Each section opens with **The answer first:** and ends with **For your project:** (as P4's reading file). It must teach every key point of every question in §5.

## 8. Verify notebook `study/notebooks/I-CMP_granularity_verify.ipynb`

Built by `sources/verification/I-CMP/icmp_build_verify_nb.py` (nbformat, P2's builder pattern: a setup cell with `check(label, got, expected, tol=None)` that prints ✓/✗ and counts, one markdown "What this verifies (lesson step N, `#id`; facts Kx)" per section, Plotly charts), run by `icmp_verify_nb_run.py` (copy P2's runner: jupyter_client, saves outputs, compact Plotly, exit 0 only if all pass). Offline, 0 API calls, about a minute. Paths: the PDF at `WS.parent / "upstream" / "RAG_Techniques" / "data" / "Understanding_Climate_Change.pdf"`; seeds `study/tools/examples/climate_seed_spans.jsonl`; chunker `recursive_spans` from `study/tools/embed_fit_check.py`; CE / comparison keys from `sources/verification/corrections/contracts_check.py` (import it). MiniLM checks skip with a reason if the model is not cached (P2 pattern). Sections and the facts each re-checks:

| § | Lesson step | Rebuilds and checks |
|---|---|---|
| 1 | `upstream` | the §2 units table, read from the upstream notebooks (skip with a reason if `upstream/` is missing): chunk sizes, units, k per notebook |
| 2 | `axes` | (no numbers) the member → axis table as a DataFrame |
| 3 | `units` | K2 all values; chart: chars per token per tokenizer |
| 4 | `sizes` | K3 heading counts; K4 N, distributions and truncation shares for all 7 arms; chart: box/strip of WordPiece tokens per arm with 128/256 lines |
| 5 | `cost` | K10 every count and USD; K11; bytes formula; chart: cost ladder (log y) |
| 6 | `budget` | K6 B, k per seed, CE@4 and CE@B, realized tokens, D-001 k = 0 for the I3 probe; K12 toy; chart: CE at k = 4 vs at B per arm |
| 7 | `cells` | K8 refused / accepted; a cell-state function `cell_state(...)` with tests for the five states |
| 8 | `targets` | K5 distinct headers, token share, truncation after header; the heat-table template as a styled DataFrame (all "not run") |
| 9 | `family` | K7 b, c, exact McNemar p per arm; K9 FWER, Holm toy, MDE values; chart: FWER vs m |
| 10 | summary | the total "N checks passed / M failed" line |

## 9. Apply-it tool `study/tools/chunker_chooser.py`

"Given my documents and my questions, which granularity arms should I test, and what will each cost?" Follows `bm25_fit_check.py` / `embed_fit_check.py`: offline, deterministic, stdlib + numpy + pymupdf + tiktoken (+ the MiniLM tokenizer from the local HF cache for WordPiece counts, optional with a clear fallback to a ρ estimate), importable (`run_check`, `render_report`) and a CLI with `--report`. **0 API calls; no embedding model is needed** (the semantic arm is proposed or not from text features, not run).

- Inputs: `--docs` (PDF, .md, .txt files or folders); `--questions` (optional JSONL `{"q", "category"?}` or .txt); `--profile` (optional JSON: `updates_per_month`, `queries_per_month`, `budget_usd`, `provider` one of `groq-gpt-oss-20b|claude-haiku-5-5`, `tpm_limit`, `tpd_limit`); `--k 4`; `--embedder minilm|cohere-v4` (sets the max length 256 or 8,192 and the tokenizer used for truncation); `--dev-n` (default: 30% of the answerable questions, else 12).
- Measures: heading detectability (PDF: bold/size spans per page as in K3; Markdown: `#` lines); page and section length distributions; ρ per tokenizer; truncation share at candidate sizes (500, 1000, 1500, 2000 chars, pages, sections); near-duplicate documents and sections (8-word shingle Jaccard ≥ 0.5, plus repeated heading names); the share of chunks that start with a pronoun or "this/it/they" (anonymous-chunk proxy); sentence count (I3 regex); numeric density; the question-category mix; index-time calls, tokens, USD and quota-days per arm (the §4 formulas; prices from `study/tools/examples/prices_2026-10-17.json` if it has them, else LLMOPS §6.2 values as constants, labelled).
- Checklist K1–K12 exactly as the research §8 table (auto / manual), each with ✓ / ✗ / ? and evidence. Recommendation logic as the research §8 (always A0; I2 if K3; I5 deterministic if K4 or K5; LLM context only if K7 passes; I3 only for long topic-shifting prose without structure; I4 only on a subset for a factoid-heavy, static corpus with K7; I6 only for a vocabulary-mismatch bucket with many queries; cut to 3 by bucket count × severity / cost). Outputs: the ranked ≤ 3 arms with reasons, a "not recommended because" list, a **pre-registration draft** (hypotheses, primary metric CE@4 at fixed k and equal B, guards, Holm α per comparison, dev/test plan, MDE at `--dev-n`), the checklist.
- Examples (committed): `study/tools/examples/climate_chooser_report.md` (Corpus D + `climate_seed_spans.jsonl` questions; it must find 33 pages, 282 headings with 192 bold-only, 11 repeated heading names, a single document so title headers are flagged useless, truncation shares matching K4 for 1000/1500/2000 and pages) and a toy Markdown corpus written for the tool, `study/tools/examples/handbook_toy/` (three short regional versions UK/US/IN of a 3-section policy handbook, near-duplicate, clean `#`/`##` headings) with `handbook_chooser_report.md`, which must recommend A0, I2, I2 + I5 and not I3/I4.
- Test: `sources/verification/I-CMP/icmp_tool_test.py` → `out_icmp_tool_test.txt` (P2/P4 pattern: unit tests of every measure on tiny inputs, the two examples regenerated byte-identically, CLI exit codes, a missing-file error, no network: the test sets `HF_HUB_OFFLINE=1` and checks no socket is opened by monkeypatching `socket.socket`).
- `study/kit.py`: the lead adds `"I-CMP": "chunker_chooser"` to `_TOOL_HINT`.

## 10. Checks the lead runs before delivery

`icmp_kit_measure.py` byte-identical rerun · `icmp_sources.py` ALL PASS · `icmp_md_check.py` (question + reading files: kit parser and lint, the 17 ids/sets/types, FORMAT rules, the interview item verbatim with notice, recomputed item data, reread links and anchors resolve into reading and lesson, reading shape and word count, banned phrases, every number traced to the facts or the item's own toy data, `quiz.py --check`) · notebook run all ✓ · tool test all pass · lesson browser tests (Playwright/Chromium: Short/Full, 7 themes × light/dark, panel left/right/hidden, T key, ↑ button, 390px with no sideways scroll, every control, quick checks, no console errors, anchors, offline) · banned phrases absent from the lesson · gap audit written.
