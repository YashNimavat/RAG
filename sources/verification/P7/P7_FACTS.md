# P7_FACTS — what the P7 lesson can rely on (run-verified)

Run date: **2026-10-08**. Every number in [`concepts/P7_grounded_prompting.md`](../../../concepts/P7_grounded_prompting.md) is listed here with the command and output section that produced it. Numbers not produced by these runs are marked CITED (from an earlier logged run), DERIVED (arithmetic shown in the lesson) or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`).
- **Versions** (printed in S1): pymupdf 1.26.7 · tiktoken 0.14.0.
- **Corpus.** `C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques\data\Understanding_Climate_Change.pdf`, SHA-256 `1d58a0fac2435c2ce4129ff84906b93118d731e4a004e7a26f8ab8f749a92669` (repo pinned at `009adba`).
- **Extraction.** Identical to the acceptance suite and P1: `page.get_text()` per page, pages joined with `"\n"`.
- **Tokenizer.** tiktoken `o200k_harmony` (= `tiktoken.encoding_for_model('gpt-oss-20b')`, S1), as in P1 D.5.
- **No API calls.** No Groq or Cohere call; `.env` is never read. The lab's optional Groq cell (Task 7) was **not** run.
- **Scripts** (this folder):

  | Script | What it produces | Saved output |
  |---|---|---|
  | `p7_measure.py` | S1–S10: P1 reproduction, prompt anatomy, lab chunks and CR-08 counts, block distribution, budget toy, repo-prompt audit, edges-first toy, citation/abstention toy, lab fingerprints. Also the **reference solution** for the lab | `out_p7_measure.txt` (stderr was empty, so no stderr file is kept) |
  | `p7_sources.py` | S-src: every cited repo cell (0-based), helper line range, caller search, book phrases and absence checks | `out_p7_sources.txt` |
  | `p7_kit_measure.py` (2026-10-18) | K1–K12 for the HTML lesson: v0's 97 chunks, the real window, the template estimate, the added answer checks, JSON toys, injection scan. `p7_measure.py` is unchanged | `out_p7_kit_measure.txt`, `out_p7_kit_measure.stderr.txt` (empty) |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P7/p7_measure.py \
      "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" "$B/upstream/RAG_Techniques" \
      > sources/verification/P7/out_p7_measure.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/P7/p7_sources.py \
      "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" \
      > sources/verification/P7/out_p7_sources.txt
  ```
- **Determinism.** Two consecutive runs of `p7_measure.py` gave byte-identical stdout.

## 1. Facts by section

`M` = `p7_measure.py` (section in `out_p7_measure.txt`); `S` = `p7_sources.py`.

### S1 Extraction

| Fact | Value | Source |
|---|---|---|
| Pages / characters | 33 / 72,593 (same as P1 S1) | M S1 |
| Encoding, vocab | `o200k_harmony`, 201,088; `encoding_for_model('gpt-oss-20b')` → `o200k_harmony` | M S1 |

### S2 P1 reproduction (consistency with P1 D.5)

| Fact | Value | Source |
|---|---|---|
| v0 prompt over the first four 1000/200 document windows: system / question / sources / user / system+user | **107 / 20 / 842 / 869 / 976** (identical to P1 S9) | M S2 |
| Same prompt with the first **eight** windows | **1,799** (P1 S10 estimated ~1,818 by adding 842 again; ×1.84 measured vs ×1.86 estimated) | M S2 |

### S3 Anatomy of the 976-token prompt

| Part | Tokens | Share | Source |
|---|---|---|---|
| System rules | 107 | 11.0% | M S3 |
| 4 block headers (9 each) | 36 | 3.7% | M S3 |
| 4 chunk texts | 803 | 82.3% | M S3 |
| Question | 20 | 2.0% | M S3 |
| Scaffolding + boundary effects (remainder) | 10 | (1.0%, DERIVED 10/976) | M S3 |

### S4 Lab chunks (hand-picked toy ranked list for D-001; NOT a retrieval result)

| Fact | Value | Source |
|---|---|---|
| CHUNKS4 = page slices (p.3 [800,1800), p.10 [0,1000), p.23 [1200,2200), p.1 [1000,2000)); CHUNKS8 adds p.6 [1389,2389), p.24 [0,1000), p.2 [0,1000), p.8 [0,1000) | all 1,000 chars | M S4 |
| D-001 gold sentence inside chunk 1 | True | M S4 |
| Distractors: p.10 slice has "2 degrees"; p.23 slice has "1.5" and "2 degrees" | True / True / True | M S4 |
| p.1 slice mentions IPCC; a year right after "IPCC" | True; False | M S4 |
| k = 4 prompt (system + user) | **958** tokens (4,661 chars); blocks incl. header 210 / 204 / 194 / 214 | M S4 |
| k = 8 prompt | **1,744**; ×1.82 | M S4 |
| Same 4 places at 2,000 chars (p.3 [183,2183), p.10 [0,2000), p.23 [204,2204), p.1 [424,2424)) | **1,695**; ×1.77; gold still inside | M S4 |

### S5 Block tokens over all per-page fixed windows (plain slices, per-page scope; not the recursive splitter)

| Config | Blocks | Mean chars | Tokens min / median / mean / max | Source |
|---|---|---|---|---|
| 1000/200 | 97 | 880 | 85 / 178 / 165.5 / 217 | M S5 |
| 2000/400 | 65 | 1,313 | 85 / 191 / 241.7 / 410 | M S5 |

Mean ratio 241.7 / 165.5 = ×1.46 (DERIVED).

### S6 Budget with answer reserve (TOY windows)

| Fact | Value | Source |
|---|---|---|
| Fixed part (v0 rules + user scaffolding + D-001 question) | 133 | M S6 |
| W = 4,096: input budget; blocks that fit at 217 / 178 | 3,456; 15 / 18 | M S6 |
| W = 8,192: input budget; blocks that fit at 217 / 178 | 7,552; 34 / 41 | M S6 |
| W = 4,096 with no reserve, at 217 | 18 | M S6 |

`max_tokens = 512` is 06 §3.1. The margin **128 is an Assumption** (P1 B.3 saw ~71 extra prompt tokens in one call).

### S7 Repo prompts: instruction tokens and audit

Texts are asserted against the pinned cells inside the script; the audit equals a manual reading written before the run (`EXPECTED` in the script).

| Prompt | Instruction tokens | context_only | refusal | cite_ids | labelled_blocks | invites_memory |
|---|---|---|---|---|---|---|
| `simple_csv_rag` 16 | 45 | F | T | F | F | F |
| `local_rag_huggingface_faiss` 22 + 24 | 53 | T | T | F | T | F |
| `helper_functions.py` L162-205 | 18 | T | F | F | F | F |
| `reliable_rag` 18 | 31 | F | F | F | T | T |
| `multi_model_rag_with_captioning` 20 | 31 | F | F | F | F | T |
| v0 (06 §3.3) | 107 | T | T | T | T | F |

DERIVED: 107 − 31 = 76 extra tokens for the v0 rules; 76 / 976 = 7.8%.

### S8 Edges-first (toy algorithm output)

| k | Prompt order of ranks | Middle | Source |
|---|---|---|---|
| 4 | [1, 3, 4, 2] | 3, 4 | M S8 |
| 5 | [1, 3, 5, 4, 2] | 5 | M S8 |
| 8 | [1, 3, 5, 7, 8, 6, 4, 2] | 7, 8 | M S8 |

k = 6 → [1, 3, 5, 6, 4, 2] in Part F is DERIVED by the same rule.

### S9 Citation and abstention toy answers (written for P7; not model outputs)

| Answer | Citations | Invalid (vs CHUNKS4) | Abstention | Source |
|---|---|---|---|---|
| A | (climate, 3) | — | False | M S9 |
| B | (climate, 3), (climate, 12) | (climate, 12) | False | M S9 |
| C (exact sentence) | — | — | True | M S9 |
| D (lower case, quotes, spaces, no full stop) | — | — | True | M S9 |
| E ("I can't answer…") | — | — | False | M S9 |
| F (uncited fact) | — | — | False | M S9 |

### S10 Lab fingerprints (`_fp` = first 16 hex of sha256 of `json.dumps(x, sort_keys=True)`)

| CHECK | Fingerprint | Value hidden |
|---|---|---|
| Task 1 stages | `05578baa00e3bdcf` | 3 index, 5 query |
| Task 2b prompt (system, user) | `6fa99768a3dfeca8` | v0 prompt for D-001 + CHUNKS4 |
| Task 2b tokens | `debc96817a3523d6` | 958 |
| Task 3 k = 8 / 2,000-char | `0c75ccaac2812081` / `35ea9e03d5f2f465` | 1,744 / 1,695 |
| Task 4 `edges_first(1..8)` | `6b966d3b7c398acc` | S8 |
| Task 6 audit | `d75f2da525a7de19` | S7 (five repo rows) |

### S-src Citations

`p7_sources.py`: **ALL PASS**, 116 checks (repo HEAD `009adba2…`).

| Citation | Checked content |
|---|---|
| `simple_csv_rag.ipynb` cell 16 | context sentence, "don't know" sentence, `"{context}"`, `create_stuff_documents_chain(llm, prompt)` |
| `local_rag_huggingface_faiss.ipynb` cells 12, 18, 20, 22, 24, 26 | `PyPDFLoader`; `k: TOP_K`; `max_new_tokens=256`, `temperature=0.1`; "using ONLY the context", refusal line, "prior knowledge"; `[Page {…}]` in `format_docs`; out-of-scope GDP question |
| `reliable_rag.ipynb` cells 18, 20 | "based upon your knowledge", `<docs>` template, `ChatGroq(llama-3.1-8b-instant, temperature=0)`, Source metadata; the hallucination grader |
| `multi_model_rag_with_captioning.ipynb` cells 12, 14, 15, 17, 20 | captioning prompt; `name` metadata, `chunk_size=400, chunk_overlap=50`; `k: 1`; BLEU query; permissive line, `ChatCohere(command-r-plus)`, `docs[0].page_content`; saved output of cell 20 states a BLEU number; cells 17–18 have no saved output; 22 cells |
| `helper_functions.py:L162-L205` | L162 `def create_question_answer_from_context_chain(llm):`; L205 return of `answer_question_from_context`; "based ONLY on the provided context"; only `helper_functions.py` calls/defines the two functions; `evaluation/evalute_rag.py` imports the chain but never calls it |
| Book phrases (each < 15 words) | Ch1 p.1, p.3, p.9 (×2), p.10 of 14; Ch3 p.5 (×2), p.6 (×2), p.8, p.11 of 14; Ch16 p.6 (×2), p.8 (×2) of 11; Ch22 p.5, p.8, p.16 of 19; Appendix p.15, p.17 of 23 |
| Book absence checks | no "lost in the middle"; no "Liu"; "appear(s/ing) first" only at Ch22 p.5/19 and Appendix p.15/23 |

### Lab test (throwaway solution kept outside the workspace)

- Runner and solution: scratchpad `test_p7_lab.py` (not in WS). It fills the learner cells, runs every code cell in order in one namespace with `RUN_GROQ = False`, and reports each CHECK.
- **Result:** 7/7 CHECK cells pass with the solution; **13/13** broken variants fail at the intended CHECK (wrong stage; rules without refusal; rules without citation format; header without parentheses; no blank line between blocks; question before sources; `fit_blocks` off by one; budget without the answer reserve; reversed edges-first; plain rank order; substring abstention; citations as strings; one audit cell wrong). The **blank** notebook fails every CHECK (missing predictions or definitions).

## 1b. Added 2026-10-18: K1–K12 (`p7_kit_measure.py`) for the HTML lesson

`K` = `p7_kit_measure.py` (section in `out_p7_kit_measure.txt`). Run from `rag_learning/`:
`PYTHONIOENCODING=utf-8 uv run python sources/verification/P7/p7_kit_measure.py "C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"`. A second run gave byte-identical stdout (`cmp`); stderr was empty. No API call, no `.env` read. `p7_measure.py` is unchanged.

**Why a second script.** The study kit's examples use v0's **97 chunks** (the 07 recursive chunker, per page, 1,000/200), as decided in `study/research/phase_01_prerequisites.md`, phase-level notes §2. The lesson also needs the real Groq window and the answer checks it adds. CHUNKS4 (S4) stays the worked prompt example: it is a hand-picked toy ranked list, not retrieval. Every toy answer, label and passage in K6–K11 was written for P7; none is a model output.

| Id | Fact | Value |
|---|---|---|
| K1 | Environment | Python 3.12.8; pymupdf 1.26.7, tiktoken 0.14.0; PDF sha256 `1d58a0fa…92669`; 33 pages; 97 v0 chunks; CHUNKS4 v0 prompt for D-001 = **958** tokens (S4 reproduced) |
| K2 | Block tokens over v0's 97 chunks (header `[1] (climate:p)` + text) | chars 393 / mean 858 / 1,000; tokens min **77**, median **171**, mean **160.7**, max **201** (S5's plain slices: 85 / 178 / 165.5 / 217). A two-digit block number adds **0** tokens (`[1] (climate:12)` and `[10] (climate:12)` are both 9) |
| K3 | Budget at the real window (Groq model page, read 2026-10-17: W = **131,072**, max output 65,536; external) | Fixed part 133 (S6). R = 512, m = 128: input budget 130,432; blocks that fit: **600** at 217 (S5 worst), **648** at 201 (v0 worst). R = 1,024 (Groq's default): 598 / 645. The 958-token CHUNKS4 prompt is **0.73%** of the window; P1's 976 is 0.74%; with ~71 template + 512 reserve, 1,541 = 1.18% (P1 K8: 1,559 = 1.19%). If one request's prompt + template + reserve had to fit in 8,000 tokens per minute (plan and counting rule UNVERIFIED), **33** blocks of 217 fit. Cost per call at the 512-token output cap ($0.075 / $0.30 per M, read 2026-10-17): k = 4 ≤ $0.000234; k = 33 ≤ $0.000706; k = 600 ≤ **$0.009934** |
| K4 | Hidden chat-template tokens, **offline estimate** from the published Harmony format (system message with identity, knowledge cutoff, date, `Reasoning: low`, channels; v0 rules in a developer message under `# Instructions`; user message; `<|start|>assistant`) | Rendered **1,032** tokens vs your text 958: overhead estimate **74** (Harmony system text 57, `# Instructions` header 3, 10 marker tokens). P1 logged ~71 in one real Groq call. How Groq renders a request is **UNVERIFIED**; the margin 128 stays an Assumption |
| K5 | Edges-first order | k = 4 [1, 3, 4, 2], middle 3, 4 · k = 5 [1, 3, 5, 4, 2], middle 5 · k = 6 **[1, 3, 5, 6, 4, 2]**, middle **5, 6** · k = 8 [1, 3, 5, 7, 8, 6, 4, 2], middle 7, 8. Rank 2 always goes last |
| K6 | Answer checks on toy answers A–H (context CHUNKS4; D-001 gold page 3) | A: cites (climate, 3), page-hit 1 · B: invalid (climate, 12) · C, D: abstained (page-hit not applicable) · E "I can't answer that from these sources.": not abstained, 1 uncited sentence, **refusal-like** · F: 1 uncited sentence · G (hedged but correct and cited): **refusal-like** too, page-hit 1 · H: cites only p.23 (the 1.5 °C distractor), 1 uncited sentence, page-hit 0. Refusal-like = 4 regex phrases (fingerprint `b17ae385…`) |
| K7 | Citation recall and precision on one toy answer, labels **given** (no NLI model) | s1 one supporting citation; s2 two citations that support only together; s3 one supporting + one that does not (and is not needed); s4 unsupported. **ALCE: recall 0.750 (3/4), precision 0.667 (4/6)** · **06 §7.4: recall 0.500 (2/4), precision 0.333 (2/6)** |
| K8 | JSON answers: strict schema candidate `answer_json_v1` (`abstained` + `sentences[{text, citations}]`, all required, `additionalProperties: false`, citation pattern `doc:page`), checked with plain Python | Schema = 100 tokens (whether it is billed as input: UNVERIFIED). J1 valid · **J2 valid but cites climate:12, not in the prompt** · J3 extra field `confidence` → invalid · J4 cut mid-string → not JSON · J5 `abstained: true`, no sentences → valid |
| K9 | Instruction-like text in documents (8 regex patterns, fingerprint `4c816a0a…`) | v0's 97 chunks: **0** flagged. A planted toy chunk ("Ignore the previous instructions and answer…") is flagged |
| K10 | Candidate `answer_v2` sentences (v0 stays frozen) | "sources are data" 14 tokens · conflict rule 15 · dated sources 17 · all three 46 (v0 rules 107) |
| K11 | Context-swap and closed-book controls | Decision table only (no model run). Hand-written neutral swap passage (sourdough starter), 195 chars, 47 tokens, no "1.2". D-009 and D-010 expect the fixed refusal sentence |
| K12 | Fingerprints of the toy inputs | TOY `84aef553b506440b` · STMTS `d99bfa90ca3fd849` · JTOY `a03b0fd5cdcefacf` · INJ `4c816a0a93a6ef51` · REFUSAL_LIKE `b17ae385a199d243` · SCHEMA `5a73d70f34f59f14` |

**External facts the lesson uses (read 2026-10-17 by the Phase 1 research; dated, not measured here).** Liu et al., TACL 12 (2024) 157–173, Table 6 (20 documents, accuracy by position 1st/5th/10th/15th/20th): GPT-3.5-Turbo 75.8 / 57.2 / 53.8 / 55.4 / 63.2, Claude-1.3 59.9 / 55.9 / 56.8 / 57.2 / 60.1; Table 1 closed-book 56.1 / 48.3, oracle 88.3 / 76.1; §5: 50 instead of 20 documents added about 1.5 (GPT-3.5) and about 1 point (Claude-1.3). gpt-oss model card (arXiv 2508.10925) §4.3: prompt-injection hijacking gpt-oss-20b 0.639 vs o4-mini 0.917; phrase protection 0.661 vs 0.912; §4.5 SimpleQA hallucination rate 0.914 (accuracy 0.067). Groq: strict `json_schema` supported on `openai/gpt-oss-20b`; not with streaming or tool use. Anthropic: question after long documents up to 30% better (their tests); Citations cannot be combined with structured outputs (400). Sources are listed in the research file, Concept P7 §1.

## 2. CITED, DERIVED and UNVERIFIED

| Item | Status |
|---|---|
| 976 = 107 + 869 (P1 S9) | CITED and re-measured (S2) |
| Empty answer at `max_tokens=12`; ~71 extra prompt tokens | CITED from P1 B.2, B.3 (session log 2026-10-08 #2; O2 report) |
| O1-Q07 score 1, O1-Q08 parametric-knowledge answer | CITED from `progress/session_log.md`, session 2026-10-08 #1 |
| Liu et al. 2023: U-shaped use by position; multi-document QA and key-value retrieval; also long-context models; TACL | Read from the arXiv abstract page (https://arxiv.org/abs/2307.03172) on 2026-10-08. No number from the paper is used. The figure, the experiments and the cause are UNVERIFIED |
| Part F, L and M arithmetic (15 blocks; 24 blocks at W = 6,000; 34 at W = 8,192; 76 tokens; ×1.46) | DERIVED in the lesson from S-numbers |
| Margin 128 tokens | Assumption |
| Groq context window for `openai/gpt-oss-20b`; behaviour at the limit | UNVERIFIED (learner looks it up, P1 lab Task 8) |
| What a model does with the permissive vs v0 prompt (Part I, lab Task 7) | UNVERIFIED; not run |
| `create_stuff_documents_chain` context formatting; `[Page n]` base (0 or 1) | UNVERIFIED (library defaults; LangChain not installed) |

## 3. Notes for 02 and 04 (not edited; recorded here and in the lesson's G.2)

- **04 P7 row:** Ch1 p.10/14 (the algorithm sketch) is missing; `local_rag_huggingface_faiss.ipynb` cell 23 is markdown (prompt = cell 22, tags = cell 24); the captioning notebook cell 20 and the book's first-position claim (Ch22 p.5/19, Appendix p.15/23) are missing. The other cells match.
- **02 P7 card:** "Ch3 p.5/14 (generate step)": p.5 holds only the heading; the text is on p.6/14. "Position effects are not in the book" is too strong: a first-position claim exists (no U-shape).
