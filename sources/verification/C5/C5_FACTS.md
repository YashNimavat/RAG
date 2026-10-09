# C5_FACTS — what the C5 lesson can rely on (run-verified)

Run date: **2026-10-08**; re-run **2026-10-09** after adding the stop flags (external-resources review §3a rows 4–5). Every number in [`concepts/C5_generation_citations.md`](../../../concepts/C5_generation_citations.md) is listed here with the command and output section that produced it. Numbers not produced by these runs are marked CITED (from an earlier logged run), DERIVED (arithmetic shown in the lesson) or UNVERIFIED.

## 0. Environment, provenance, how to re-run

- **Interpreter.** CPython 3.12.8 (Windows 11), the project uv environment (`rag_learning/.venv`). Nothing was installed.
- **Versions** (printed in S1): pymupdf 1.26.7 · tiktoken 0.14.0 · numpy 2.5.3 · sentence-transformers 6.1.0 · groq 1.7.0 (SDK inspected, never called).
- **Corpus.** `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, SHA-256 `1d58a0fa…92669` (repo pinned at `009adba`). Extraction as in the acceptance suite: `page.get_text()` per page, pages joined with `"\n"`.
- **Retrieval fixture.** The v0 chunks (per-page recursive 1,000/200 spans from 07 H.1/H.3, loaded through the acceptance suite's `contracts_check.load_07_modules`, read-only), with the **course chunk ids** (`params_hash` over 06 §2.4's chunking block, as in the C2 lab and C4). Ranked by local `sentence-transformers/all-MiniLM-L6-v2` (HF cache, offline), exact cosine, ties by `chunk_id`. This reproduces C4's D-002 top-4. It uses the **fallback** embedder, so it is **not** the v0 default (Cohere `embed-v4.0`) and **not** an evaluation result.
- **Tokenizer.** tiktoken `o200k_harmony` (= `encoding_for_model('gpt-oss-20b')`, P1/P7).
- **No API calls.** No Groq or Cohere call; `.env` never read. The Groq call is exercised with `FakeGroq` (a stand-in shaped like groq 1.7.0's response). The lab's optional Task 9 was **not** run, so every real model answer is UNVERIFIED.
- **Scripts** (this folder):

  | Script | What it produces | Saved output |
  |---|---|---|
  | `c5_measure.py` | S1–S10: snapshot, chunk ids, retrieval fixture, template and token counts, fake call, toy answers, diagnosis key, CR-08 probes, record shape, lab fingerprints. Also the **reference solution** for the lab | `out_c5_measure.txt`; `out_c5_measure.stderr.txt` (model-loading progress bar only) |
  | `c5_sources.py` | S-src: every cited repo cell (0-based), helper lines, repo-wide parser scan, book phrases and absence checks, groq SDK signature and docstrings | `out_c5_sources.txt` |
  | (outside the workspace) 2026-10-08: `scratchpad/c5/run_lab.py` + `solution.py` + `make_lab.py`. 2026-10-09: copies in a later session's `scratchpad/g2c5/lab_test/` (same `run_lab.py`; `solution.py` with the stop flags and 3 more broken variants), and `scratchpad/g2c5/patch_lab.py`, which edited lab cells `c5-19`, `c5-22`, `c5-24` in place (`make_lab.py` was not re-run) | LT: builds the lab, runs it with a throwaway solution, blank, and 34 broken variants | `out_c5_lab_test.txt` |

- **Re-run** (from `rag_learning/`, Git Bash):
  ```bash
  B="C:/Yash/New-Work/Book RAG"
  PYTHONIOENCODING=utf-8 uv run python sources/verification/C5/c5_measure.py \
      "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
      > sources/verification/C5/out_c5_measure.txt 2> sources/verification/C5/out_c5_measure.stderr.txt
  PYTHONIOENCODING=utf-8 uv run python sources/verification/C5/c5_sources.py \
      "$B/upstream/RAG_Techniques" "$B/RAG_Made_Simple_The_Complete_Visual_Guide" \
      > sources/verification/C5/out_c5_sources.txt
  ```
- **Determinism.** Two consecutive runs of `c5_measure.py` gave byte-identical stdout.
- **File hashes at the time of the run** (sha256): 2026-10-08: `c5_measure.py` `a6784359…`, `c5_sources.py` `7c57b813…`, `labs/C5_generation_lab.ipynb` `928e00e6…`. 2026-10-09 re-run: `c5_measure.py` `54784e8c…`, `c5_sources.py` `8b2c8653…`, `labs/C5_generation_lab.ipynb` `d350cb0e…`.
- **Label → chunk id.** Answers carry the template's labels `[doc_id:page]`; `check_citations` maps each label to every retrieved chunk id on that `(doc_id, page)`, in rank order. Chunk ids never appear in answers.

## 1. Facts by section

`M` = `c5_measure.py` (section in `out_c5_measure.txt`); `S` = `c5_sources.py`; `LT` = lab test.

### S1 Snapshot

| Fact | Value | Source |
|---|---|---|
| Pages / characters | 33 / 72,593 | M S1 |
| `doc_text_sha256`; `snapshot_id` by the 06 §5.3 recipe | `5106772e…7368c6`; **`ea07572562ac`** (equals 06 §5.3) | M S1 |

### S2 Chunks and ids

| Fact | Value | Source |
|---|---|---|
| v0 per-page recursive 1000/200 chunks | **97** chunks, one page segment each | M S2 |
| Course `params_hash` (sha256 of the 06 §2.4 chunking block, 12 hex) | `1ca9c5a3b548` | M S2 |
| Chunk id format (06 §2.3) | `climate:ea07572562ac:1ca9c5a3b548:00000` | M S2 |
| `chunks.jsonl` sha256 equals the C2 lab / C4 file `d4108b89…` | True | M S2 |

### S3 Retrieval fixture (MiniLM fallback; demo only)

| Fact | Value | Source |
|---|---|---|
| D-002 top-4 (rank: seq, page, score) | 1: 69 p.24 0.4606 · 2: 68 p.23 0.4513 · **3: 27 p.10 0.4386** · 4: 17 p.6 0.4385 (= C4 S3 [69, 68, 27, 17]) | M S3 |
| D-002 chunk lengths (characters) | 982, 657, 951, 823 (DERIVED from the offsets) | M S3 |
| D-002 gold quote (p.10) inside which rank | **3** only; "2015" appears only in rank 3 | M S3 |
| D-002 ranks 5–8 | p.29 0.3387 · p.29 0.3114 · p.24 0.2567 · p.12 0.2448 | M S3 |
| D-009 top-4 (seq, page) | 85 p.29 · 27 p.10 · 69 p.24 · 84 p.29 (ranks 1 and 4 share p.29) | M S3 |
| "IPCC" on pages; "1988" in the PDF; p.1 in D-009 top-4 | [1]; False; False | M S3 |
| Answerable seeds (8) with a gold **page** in their top-4 | 8 of 8 (page level only, not span coverage) | M S3 |

### S4 Template, messages, tokens (`o200k_harmony`)

| Fact | Value | Source |
|---|---|---|
| Template system part == P7 `SYSTEM_V0` | True | M S4 |
| `sha256(ANSWER_V1_TXT)` | `739752dc…351a4f`; one extra space changes it | M S4 |
| P7's lab chunks through the template file | **958** (= P7 S4) | M S4 |
| D-002, k = 4: system / user / system+user / sources (`context_tokens`) | 107 / 695 / **802** / 680 | M S4 |
| D-002, k = 4: block tokens incl. header | 199 / 133 / 196 / 152 | M S4 |
| Shuffled input → same messages after rank sort | True | M S4 |
| `prompt.sha256` (D-002, k = 4) | `820b2956…79c1f0dd` | M S4 |
| D-002, k = 8: system+user; ratio | **1,442**; ×1.80 | M S4 |
| D-009, k = 4: system+user | 858 | M S4 |
| 10 seed prompts, k = 4: min / max / sum | 771 / 894 / **8,427** | M S4 |

### S5 The call (FakeGroq; no network)

| Fact | Value | Source |
|---|---|---|
| Keyword arguments sent | `model`, `messages`, `temperature` 0.0, `max_tokens` 512, `reasoning_effort` "low" | M S5 |
| Reply `""`, `None`, whitespace, `""` with `finish_reason="length"` | AssertionError in all 4, message names `finish_reason` | M S5 |
| `completion_tokens_details=None` | `reasoning_tokens` → None, no crash | M S5 |
| Non-empty cut-off reply (hand-written toy) `"The Paris Agreement was adopted in 2015 [climate:10]. It aims to limit warming to"`, `finish_reason="length"`, through `call_llm` and `make_record` (2026-10-09) | `call_llm` passes; flags `length_stop`, `uncited_sentence`; `citation_subset_ok` True; `failing_qids` → `[]` | M S5 |
| `make_answer` on the T01 text with `finish_reason` "stop" / "length" / "tool_calls" / `None` (2026-10-09) | `[]` / `length_stop` / `unexpected_finish_reason` / `unexpected_finish_reason` | M S5 |

### S6 Hand-written toy answers (not model outputs), D-002 top-4 unless noted

The toy answers keep `make_answer`'s default `finish_reason="stop"`, so the stop flags never fire here; every S6 row and the S10 Task 5 fingerprint were unchanged by the 2026-10-09 re-run.

| Toy | Result (flags; `citation_subset_ok`) | Source |
|---|---|---|
| T01 `…2015 [climate:10].` | no flags; True; resolves to chunk 00027; unused 00069, 00068, 00017 | M S6 |
| T02 `[climate:12]` · T03 `[paris:10]` · T04 `[Climate:10]` | `cited_not_retrieved`; False | M S6 |
| T05 no tag | `no_citation`; **True** | M S6 |
| T06 one of two sentences cited | `uncited_sentence` (1); True | M S6 |
| T07 `[4]` · T08 `[climate: 10]` · T09 `(climate:10)` · T10 `[climate:10, climate:24]` | `malformed_tag` + `no_citation`; False | M S6 |
| T11 tag after the full stop | no flags; uncited 0 | M S6 |
| T12 `[climate:10][climate:24]` | no flags; True; unused 00068, 00017 | M S6 |
| T13 exact abstention · T14 lower case, quotes, spaces | abstained; no flags; True | M S6 |
| T15 paraphrased refusal | not abstained; `no_citation` | M S6 |
| T16 abstention sentence + `[climate:23]` | `abstention_inside_answer`; True | M S6 |
| T17 empty | `empty`; True | M S6 |
| T18 D-009 abstention | abstained; unused = all 4 | M S6 |
| T19 D-009 `…1988 [climate:29].` | **no flags; True**; resolves to 00085 **and** 00084 | M S6 |

### S7 Diagnosis key (lab Task 7, lesson Part J)

| | Kind | Caught by (v0) |
|---|---|---|
| a cites p.12 (gold p.10 at rank 3) | generation | subset check |
| b p.24/23/6 unused | none | nothing to catch |
| c D-009 "1988 [climate:29]" | generation | not caught in v0 |
| d gold missing, abstained | retrieval | retrieval metric |
| e "2016 [climate:23]" (flags `[]`, subset True) | generation | not caught in v0 |
| f gold missing, correct, no tag | both | `no_citation` flag |

### S8 CR-08

| Fact | Value | Source |
|---|---|---|
| T01 unused at k = 4 / k = 8 | 3 of 4 / **7 of 8** | M S8 |
| TOY window 8,192, margin 128: input budget at `max_tokens` 512 / 256 | 7,552 / 7,808 | M S8 (arithmetic) |
| 10-query run: output cap total at 512 | 5,120 tokens (upper bound) | M S8 |

The **effect** of `max_tokens=256` on real `gpt-oss-20b` answers is **UNVERIFIED** (no call made). CITED: at `max_tokens=12` the O2 smoke call returned an empty answer (session log 2026-10-08 #2).

### S9 Record shape

The full JSON record for T01 via FakeGroq is printed in M S9 (keys `qid`, `question`, `context`, `prompt`, `llm`, `answer`, `latency_ms`, `errors`). `failing_qids` on toy records T01, T02, T05 (with an error added), T07, T13, T12 → `['T02', 'T05', 'T07']`.

### S10 Lab fingerprints (`_fp` = first 16 hex of sha256 of `json.dumps(x, sort_keys=True)`)

| CHECK | Fingerprint |
|---|---|
| Task 1 messages / `tokens_k4` / template sha | `820b2956c6ec6f35` / `477f4b2cdd3fe2b9` / `1dd899a0d65f877a` |
| Task 3 parse T10 | `48e8934be17570b4` |
| Task 4 check D-009 T19 | `d198d0a723892dc6` |
| Task 5 all 19 toy answers | `3133756f8e11d25f` |
| Task 7 kinds / caught_by | `694ce518d388e59b` / `f59019086a14da25` |
| Task 8 `tokens_k8` / `unused_k8` | `8fd238119777a31e` / `7902699be42c8a8e` |

### LT Lab test

Throwaway solution: **8/8** CHECK cells pass; Task 9 prints "skipped". Blank notebook: **8/8** CHECK cells fail. Broken variants: **34/34** fail at the intended CHECK (e.g. no rank sort, hardcoded model, no empty assert, lenient tag regex, silent drop of unknown citations, first same-page chunk only, case-sensitive abstention, paraphrase counted as abstention, failing_qids ignoring errors, wrong diagnosis labels). The 3 added on 2026-10-09 all fail CHECK 6: cut-off answer not flagged; "length" also flagged as unexpected; `make_record` not passing `finish_reason` to `make_answer`.

### S-src Citations

`c5_sources.py`: **ALL PASS**, 127 checks (repo HEAD `009adba2…`; 125 on 2026-10-08, 2 SDK checks added 2026-10-09).

| Citation | Checked content |
|---|---|
| `simple_rag.ipynb` cells 13, 15, 17; all code cells | `k: 2`; retrieve and show context; `evaluate_rag`; no code cell builds or invokes a chat model; 22 cells |
| `local_rag_huggingface_faiss.ipynb` cells 22, 24, 26, 28 | context-only prompt with no citation request; `[Page …]` blocks; `split("Answer:")[-1]`; `RunnableParallel(answer=rag_chain, sources=retriever)` and "Sources used:"; cells 26 and 28 have no saved output |
| `crag.ipynb` cells 20, 22 | `generate_response` asks to append sources with links; `retrieve_documents` returns page_content only; local source = `("Retrieved document", "")` |
| `reliable_rag.ipynb` cells 18, 22, 23 | permissive answer prompt; `PydanticOutputParser(HighlightDocuments)`, `mixtral-8x7b-32768`, "exact match" instruction; output "ID: doc3"; no code checks a segment against the document |
| `graph_rag_local_attribution.ipynb` cells 0, 9, 17, 19 | Ollama; `re.findall(r'\[(\d+)\]')`, `set(...)`, `if key in source_map:` with no else (silent drop), `confidence=0.9`; "sources verified" print; no saved outputs |
| Repo-wide scan | only `graph_rag_local_attribution.ipynb` cell 9 runs `re.findall` on a `[` pattern; `evaluation/evaluation_grouse.ipynb` cell 30 holds a judge rubric for citations |
| `helper_functions.py:L162-L205` | no citation or source handling |
| Book phrases (each < 15 words) | Ch1 p.9, p.10 of 14; Ch3 p.6, p.8 (×3), p.9, p.11 of 14; Ch19 p.8/10 (×2); Ch22 p.7, p.8 (×2) of 19; Appendix p.5, p.21 of 23 |
| Book absence checks | "don't know" only at Ch3 p.11/14; no "abstain"; no inline `[doc:page]` format; Ch19 never says "cite" |
| groq 1.7.0 SDK | `create()` accepts `max_tokens`, `max_completion_tokens`, `reasoning_effort`; `max_tokens` documented as deprecated in favour of `max_completion_tokens`; gpt-oss supports low/medium/high, default medium; `finish_reason` may be `length`; `usage.completion_tokens_details.reasoning_tokens` exists (optional). Added 2026-10-09: `reasoning_effort` defaults to the SDK's `Omit` sentinel, so an omitted field is not sent and the default is applied by the server; the `finish_reason` Literal is exactly `stop`, `length`, `tool_calls`, `function_call` |
| Groq API reference, chat completions (https://console.groq.com/docs/api-reference), **read 2026-10-09** (web page, not a script check) | `reasoning_effort`: gpt-oss-20b and gpt-oss-120b support 'low', 'medium' or 'high', and 'medium' is the default value; values outside a model's set are rejected with a 400. The page lists no `finish_reason` values (only `"stop"` in its example). Server behaviour when the field is omitted is documented, **not measured** |
