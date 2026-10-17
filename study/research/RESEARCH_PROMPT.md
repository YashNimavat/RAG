# Phase research brief: find what each phase is missing

**What this is:** the full instructions for one research session, which covers **one phase** of the RAG course. Read this whole file before you start.
**What this is not:** permission to write lessons, notebooks or tools. This session **researches and plans only**; building comes later, after Yash approves.

---

## For Yash: how to start each session

Open a **new** Claude Code session in `C:\Yash\New-Work\Book RAG` and paste one line. Use one session per line.

| Session | Paste this |
|---|---|
| **0 (first)** | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do Session 0, the LLMOps foundation (section 0).` |
| 1 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 1 only.` |
| 2 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 2 only.` |
| 3 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 3 only.` |
| 4 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 4 only.` |
| 5 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 5 only.` |
| 6 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 6 only.` |
| 7 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 7 only.` |
| 8 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 8 only.` |
| 9 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 9 only.` |
| 10 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 10 only.` |
| 11 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 11 only.` |
| 12 | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the research for Phase 12 only.` |
| 13 (last) | `Read rag_learning/study/research/RESEARCH_PROMPT.md fully, then do the consolidation session (section 9).` |

**Order:**
1. **Session 0 first.** It writes the LLMOps foundation that every phase session applies.
2. Sessions 1–12 in any order; they do not depend on each other.
3. Session 13 last.

---

## 0. Session 0: the LLMOps foundation (run this first)

**Your job:** research once what every phase will reuse, so the phase sessions only add what is specific to their topics. Read sections 2, 3 (items 1–8 and the skills table), 5 and 6 below first. Then write **`rag_learning/study/research/LLMOPS_FOUNDATION.md`** with these sections:

1. **The lifecycle for this course.** Analyze → Measure → Improve, and dev → CI → production monitoring, mapped onto the course's version cards (06: v0 … v7) and onto the project skills in `.claude/skills/`.
2. **Response caching and replay (top priority).** Yash's API credits come and go, so **every** external call must be saved and replayable. Design it to cover:
   - **What gets cached:** LLM calls (Groq, Claude), embeddings (Cohere), reranker calls, and calls made through LangChain.
   - **The cache key:** the provider, the exact model id and version, every request parameter (temperature, max tokens, reasoning effort, tools, response format), and the full messages or input, all hashed.
   - **What gets stored:** the request, the response, usage (tokens), cost, latency and a timestamp.
   - **Where it lives:** SQLite or JSONL. Recommend whether it is committed or git-ignored, with the reason; it must never hold book text.
   - **Three modes:**
     - `record`: call the API and save the response;
     - `replay`: never call; serve from the cache, and on a miss stop with a clear message;
     - `auto`: cache first; call only on a miss when a key exists and credits remain.
   - **Detecting "no credits" or limits:** the Anthropic and Groq error types for exhausted credits and rate limits (from their docs), and the automatic switch to replay.
   - **How LangChain's own cache works** (`set_llm_cache` and friends) with chat models and tool calls: its limits, and whether to use it or wrap the clients instead.
   - **How the course's existing embedding cache fits in** (C3's `embed_hash`).
   - **Determinism:** temperature 0, why reasoning models still vary, and what replay guarantees.
   - **How cached traces feed the D-10 end-of-course judge batch.**
3. **Tracing.** LangSmith (hosted) vs Arize Phoenix vs self-hosted Langfuse vs a plain JSONL trace. Pick a default and a local option. Say what every trace must capture (`llm-observability`), and how book text is kept out.
4. **Datasets and experiments.** The golden-set lifecycle, LangSmith datasets vs local JSONL, versioning, and a leakage check (`ci-cd-evals`).
5. **Evaluators.** Code-based first, then judges under D-10, then judge validation (`code-based-evaluators`, `llm-as-judge`, `judge-validation`, `rag-evaluation`).
6. **Cost, latency and model choice.**
   - Token and cost accounting, from cached usage too.
   - Budgets per run.
   - Model tiers: Groq as the default; Claude models per task tier, with current ids and prices checked through the `claude-api` skill or Anthropic's docs.
7. **Prompt and config versioning,** and how each change is tied to an experiment.
8. **CI and monitoring with local git only** (no remote): pre-commit, pytest or nox, and a simple monitoring view.
9. **Framework guidelines:** when LangChain or LangGraph add value over plain Python, which defaults hide behaviour the lessons warn about, how to pin versions, and how to handle API churn.
10. **One shared helper package, as a plan only:** for example `rag_learning/study/llmops/` with `cache.py`, `trace.py`, `cost.py`, `evals.py`. Every LLMOps notebook imports it, so no notebook re-implements caching or tracing.
11. **Tools list,** using the table in section 6: `langchain-core`, `langgraph`, `langsmith`, `langchain-groq`, `langchain-anthropic`, `langchain-cohere`, `arize-phoenix`, `langfuse`, `anthropic` and the rest, with versions, size, offline use, licence, and the keys or accounts needed.
12. **The application map:** which LLMOps practices apply to which phase and concept, as a table. The phase sessions use it to decide what each concept's LLMOps notebook covers.

Use primary sources: the official docs and source code of each tool, and the provider docs. Follow the facts, copyright and privacy rules in section 2. Install nothing, and call no API.

---

## 1. Your job, in one paragraph

You audit one phase of the course the way concept P3 was audited. For **every concept** in your phase:
1. List every idea the concept needs, from the book pages, the existing course files, the quiz questions and current outside knowledge.
2. Check whether each idea is actually taught before it is used.
3. Research the topic online from primary sources: the papers, the official library docs, and how production systems do it.
4. Plan the **five deliverables**:
   - the lesson (theory and step-by-step explanation);
   - a verify notebook;
   - an apply-it tool, with its checklist;
   - an **LLMOps notebook**: the technique built with LangChain or LangGraph where that fits, then traced, evaluated and monitored as it would run in production;
   - the quiz.
5. List exactly which frameworks, libraries, models and LLM features each concept needs, and whether they fit the project's decisions.

You write **one file**: `rag_learning/study/research/phase_NN_<short-name>.md`, using the template in section 7.

## 2. Ground rules (non-negotiable)

1. **Read `C:\Yash\New-Work\Book RAG\CLAUDE.md` first and obey it.**
2. **Research only.**
   - Create only your output file (plus scratch files in your session's scratchpad).
   - Do not edit any existing file. That includes lessons, question files, 02, 04, 06, 08, `progress/*`, `reviews/*`, `upstream/`, the book and `study/app/*`.
   - Install nothing, and make no commits.
3. **Never ask Yash whether to include a piece of theory.** If a concept needs it, it is in scope; deciding that is your job. Ask only about real preferences, and list those questions at the end of your file.
4. **Facts.**
   - Never invent a page, a notebook cell, a paper, a number or a URL.
   - Open every book page, repo cell and URL you cite. Anything you could not check gets the label **UNVERIFIED**.
   - Label outside material as external.
5. **Copyright.**
   - The book (`RAG_Made_Simple_The_Complete_Visual_Guide/`) and the AI Eval book (`rag_learning/AI Eval/`) are copyrighted. Paraphrase them, cite pages (`Ch12 p.5/14`, `AE Ch3, 'section'`), and **never copy 15 or more consecutive words**.
   - Extract book text only into your scratchpad, and delete it at the end.
   - The two MIT repos in `upstream/` may be quoted, with their licence notice.
6. **Project decisions you must respect** (08 Part 4; CLAUDE.md):
   - **LLMs:** Groq is the default, with the model from `.env` `GROQ_MODEL_ID` (currently `openai/gpt-oss-20b`, a reasoning model).
     - The **Claude API** may be used when Yash has credits (D-32). Pick the model per task: a small, fast model for high-volume steps (query rewriting, proposition extraction, grading many chunks); a larger model where quality decides the result (final answers, judge prompts in the end batch, hard reasoning).
     - Check current Claude model ids and prices with the `claude-api` skill or Anthropic's docs. Never guess them.
     - Estimate the calls and the cost per run for every plan.
   - **Frameworks (D-32):** LangChain, LangGraph and LangSmith are in scope, **after** the plain-Python mechanism.
     - The lesson and the verify notebook stay framework-free; the LLMOps notebook uses the frameworks.
     - LangSmith is hosted, so traces leave the machine. Always offer a local option too: Arize Phoenix, self-hosted Langfuse, or a JSONL trace file.
   - **Privacy:** never plan to send text from either book to an external API or tracing service. The course corpus (the repo's climate PDF) may be sent.
   - **Embeddings:** Cohere `embed-v4.0` by default; local MiniLM (`sentence-transformers/all-MiniLM-L6-v2`) as the fallback.
   - **Not used:** OpenAI, Ollama.
   - **Judge:** automated LLM judging runs **once at the end** on stored traces (D-10). Until then, use deterministic metrics and human labels.
   - **Environment:** Python 3.12 via `uv`, CPU torch, `pymupdf==1.26.7` pinned. Local first; local git only.
   - If a technique normally needs something outside these decisions (OpenAI, a GPU, a hosted graph database, a paid SaaS), find a compatible alternative, or mark it **"needs a decision"** with the trade-off explained.
7. **Never print `.env` values.** Make no Groq, Cohere, Claude or LangSmith calls: this is research, not measurement.
8. **Writing style for your file:** plain English, short sentences, tables where they help. Follow `rag_learning/visual-learning-writer/references/WRITING_STYLE.md`.
9. **Every external call is cached (D-32).** Every plan that calls an LLM, embedder or reranker uses the shared cache-and-replay layer from `LLMOPS_FOUNDATION.md`.
   - Every notebook and tool must run **fully in replay mode**, with no key and no credits, once its responses have been recorded.
   - State which calls each plan records, and roughly how many.

## 3. Read first, in this order

**Phase sessions (1–12):** read `rag_learning/study/research/LLMOPS_FOUNDATION.md` right after CLAUDE.md. **If it does not exist, stop** and tell Yash to run Session 0 first.

1. `C:\Yash\New-Work\Book RAG\CLAUDE.md`
2. `rag_learning/README.md`
3. `rag_learning/02_RAG_MASTER_LEARNING_PLAN.md`: every card in your phase (outcomes, book pages, repo cells, failure, lab, version), plus §4 mastery gates.
4. `rag_learning/03_RAG_CONCEPT_DEPENDENCY_MAP.md`: prerequisites and families.
5. `rag_learning/04_BOOK_TO_CODE_MAPPING.md`: your concepts' rows. Known to contain errors, so verify, never trust.
6. `rag_learning/06_RAG_PROJECT_AND_EVALUATION_PLAN.md`: the version cards for your phase (v0 … v7) and the eval plan.
7. `rag_learning/08_GAP_ANALYSIS_AND_DECISIONS.md`: Part 4, decisions; Part 7, gates.
8. `rag_learning/sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md`: what it says about your concepts (AI Eval book mapping, interview repo items).
9. **The P3 pilot**, which is the quality bar you are aiming for:
   - `rag_learning/study/lessons/P3_bm25.html`, the lesson, with this order: the answer first → the theory in one read → formula sheet → steps → verify → apply → check;
   - `rag_learning/study/lessons/P3_bm25_gap_audit.md`, **the method in action**: copy its approach;
   - `rag_learning/study/notebooks/P3_bm25_verify.ipynb` and `rag_learning/study/tools/bm25_fit_check.py`, the verify notebook and the apply-it tool;
   - `rag_learning/study/FORMAT.md`, the question-file format and its rules.
10. `rag_learning/visual-learning-writer/SKILL.md` and its `references/`: the lesson writing and visual rules.
11. `rag_learning/progress/concept_tracker.csv` and `progress/misconception_log.md`: what Yash has and has not studied, and their open mix-ups.
12. For each concept, whatever already exists: `concepts/<ID>_*.md`, `study/reading/<ID>_*.md`, `study/questions/<ID>_questions.md`, `labs/<ID>_*.ipynb` and `sources/verification/<ID>/`.
13. **The project skills** in `C:\Yash\New-Work\Book RAG\.claude\skills\`. They hold the evaluation and LLMOps methods that the LLMOps notebook must follow.
    - **Load** the skills listed for your phase with the Skill tool; read any others you need from their files.
    - They come from the AI Eval book's methods, so the copyright rule applies: paraphrase, never copy.

| Skill | What it gives you | Phases where it matters most |
|---|---|---|
| `evals-foundations` | the Analyze → Measure → Improve lifecycle; what to measure | every phase (its LLMOps section), 3 |
| `rag-evaluation` | retrieval vs generation metrics, context swapping | 1 (P6), 3, 4–8 |
| `synthetic-data-generation` | building test questions by dimensions | 3 (M1), 4–7 |
| `error-analysis` | failure taxonomy from traces (open, then axial coding) | 3 (M5), every phase's failure section |
| `trace-data-analysis` | patterns across many traces | 3, 9 |
| `code-based-evaluators` | deterministic checks and a cheap-to-expensive cascade | 3, 8, 9 |
| `llm-as-judge` | binary judges, bias control | 3 (M3), 8 (end batch only, D-10) |
| `judge-validation` | TPR/TNR and corrected success rates | 3, 8 (V4) |
| `collaborative-annotation` | labelling agreement (κ) | 3 (M1) |
| `human-review-interfaces` | fast trace-review UIs | 3, 9 |
| `llm-observability` | tracing platforms and what to capture | every LLMOps notebook, 9 (D1) |
| `ci-cd-evals` | golden set, regression CI, online monitoring | 3 (M4), 9 (D3) |
| `safety-evals` | prompt injection, PII, guardrails | 9 (D4), 10 |
| `improving-llm-agents` | accuracy and cost improvements (caching, cascades) | 4–10, 9 (D2) |
| `tool-use-evaluation` | tool-calling agent evaluation | 10 (A1, A5) |
| `multi-turn-evaluation` | conversation-level evaluation | 10 (A4, A5), 12 |
| `visual-learning-writer` | lesson writing and visuals | every phase (lesson blueprint) |

## 4. The method, per concept (the P3 gap audit)

1. **Collect every idea the concept uses.** Pull them from:
   - the book pages, which you open and read;
   - the existing lesson, reading file and lab;
   - every quiz key point and wrong answer;
   - the repo notebooks cited in 02/04;
   - what the external research shows a learner must know.
2. **For each idea, record four things:**
   - where it is used;
   - whether it is **taught before use** (where, or "missing" / "incomplete");
   - which concept owns it;
   - whether Yash has studied that concept (the tracker; "written" is not the same as "studied").
3. **Classify each idea:**
   - **core:** this concept's own idea; teach it fully;
   - **bridge:** owned elsewhere, but needed here; teach it briefly, in the place it is needed;
   - **next:** belongs to a later topic; link only.
4. **Check the quiz.** If a question file exists, every key point must be answerable from the **Short** version of the lesson. List the ones that are not. If no question file exists, list the questions the concept needs (R/A/T, plus one interview item), as titles only.
5. **Find errors in what exists:** wrong pages or cells in 02/04, claims in existing lessons that the research contradicts, and outdated library behaviour. **Report them; do not edit.**
6. **Write the lesson blueprint** in the four-part structure:
   - the five-sentence answer first;
   - the theory in one read: about 8–12 linked ideas, each with its formula;
   - the formula-sheet items;
   - the step-by-step outline: one running example from the course corpus (`upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`, unless the concept needs other data; say why);
   - the visuals that earn their place: hand-drawn SVG charts or diagrams, each with the one thing it shows;
   - what belongs in Full only.
7. **Write the verify notebook plan:** which numbers and charts it recomputes, from which data and with which code. Note whether it needs an LLM or API call (and how many), whether it works offline, and its rough runtime. Interactive charts use Plotly.
8. **Write the apply-it tool plan:** what it checks on Yash's own documents and questions, its inputs and outputs, and **the real-world checklist** of 8–12 checks, each marked auto (the tool measures it) or manual (with how to check). Add the recommendation logic.
9. **Write the LLMOps notebook plan:** the concept as it would run in production, after the mechanism is understood.
   - **Apply `LLMOPS_FOUNDATION.md`;** do not redo its general research. Add only what is specific to this concept, and use its application map.
   - **Caching:** list every external call the notebook makes (provider, model, how many). Confirm the notebook runs in replay mode with no credits, using the shared helper package.
   - **Build it with a framework** where that fits: LangChain components (loaders, splitters, retrievers, rerankers, chains), or a LangGraph graph for multi-step flows (routing, corrective loops, agents). Map each framework piece to the lesson's mechanism step, and name every framework default that the lesson warns about.
   - **Trace every run:** inputs, the retrieved chunks with their scores, prompts, model and version, outputs, tokens, latency, cost. Use LangSmith, and give the local option too (`llm-observability`).
   - **Dataset and evaluators:**
     - a small golden set (taken from the course eval set once it exists), stored as a dataset;
     - code-based evaluators first; LLM judges only under D-10 (`code-based-evaluators`, `llm-as-judge`, `judge-validation`);
     - an experiment comparing this concept's version with the previous version (the 06 version cards).
     - Keep retrieval metrics and answer metrics separate (`rag-evaluation`).
   - **Track and compare:** cost per question, p50/p95 latency, token use, and the metric changes per version.
   - **Prompt and config versioning:** where prompts and parameters live, and how each change is tied to an experiment.
   - **Monitoring and feedback:** what to watch online and what triggers an alert, and how a failure flows back into error analysis and the golden set (`ci-cd-evals`, `error-analysis`).
   - **Its place in the LLMOps lifecycle:** Analyze → Measure → Improve, and dev → CI → production monitoring. Name the project skill that covers each part.
   - **A concept with no LLM in it** (for example P3, BM25) still gets this notebook: trace the retrieval runs, log the metrics per version, and wire a regression check.
   - **The RAG variants the book teaches** (reliable RAG, corrective RAG, Self-RAG, adaptive routing, Graph RAG …) each get their own LLMOps notebook. Plan how to track each one's responses, intermediate decisions (grades, routes, retries) and failures.

## 5. External research: how

- **Use web search and fetch.** Prefer, in this order:
  1. the original paper (arXiv, ACL, SIGIR…);
  2. official library documentation and source code;
  3. engineering write-ups from teams that run the technique in production;
  4. reputable surveys and textbooks;
  5. blogs, only to point you to 1–4.
- For each source, record the title, authors, year, URL, **what was actually tested, the result, and its limits**. Keep the study separate from your own interpretation.
- **Current practice:** how the technique is done today (2024–2026), which defaults libraries use, and what changed since the original paper.
- **Pitfalls and failure modes**, with evidence.
- **How to evaluate it:** which retrieval or answer metric shows whether it helps, and the baseline to compare against. Keep retrieval quality separate from answer quality.
- **Interview angle:** the 3–5 questions an AI-engineer interview typically asks about it. Check `upstream/AI-Engineer-Interview-Questions/` (MIT) first.
- Cap web research at about 25 sources per phase. Depth on the important ones beats a long list.

## 6. Tools, frameworks, libraries and LLMs: what to list

For **every concept**, fill this table (template, section 7):

| Purpose | Library / model / service | Version (pin a released version ≥ 2 weeks old) | Installed now? | Works offline? | Cost / API calls | Licence | Fits the decisions? |
|---|---|---|---|---|---|---|---|

- Cover: Python libraries; models (embedding, reranker, NLI, vision…); LLM features needed (tool calling, JSON mode, long context, reasoning effort); vector stores or databases; evaluation libraries; frameworks (LangChain, LlamaIndex, LangGraph, DSPy…); observability or CI tools; system tools.
- **Frameworks:** the course teaches mechanism first. Say whether a framework is needed at all, or only useful for **reading** the upstream repo. Prefer plain Python plus small libraries.
- For LLM features, check that the configured Groq model supports them, using Groq's official docs. Mark UNVERIFIED if you cannot confirm.
- **Always include rows for:**
  - the LLM per task: the Groq model, and a Claude model when it is worth it, with the reason and the cost per run;
  - the LangChain and LangGraph packages the LLMOps notebook needs (`langchain-core`, `langgraph`, and provider packages such as `langchain-groq`, `langchain-anthropic`, `langchain-cohere`, `langchain-community`);
  - `langsmith`;
  - the local tracing option.
- **Accounts and keys:** list the ones needed (`ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY`…). Yash adds them to `.env` when needed; never ask for their values.
- Give the install line in project form (`uv add <pkg>==<ver>`), but **do not run it**.
- Flag anything heavy (above about 500 MB, GPU-only, or a server to run) and propose a lighter option.

**The current environment** (from `pyproject.toml`, 2026-10-17): Python 3.12; `cohere`, `groq`, `nbformat`, `numpy`, `pandas`, `plotly`, `pymupdf==1.26.7`, `python-dotenv`, `rank-bm25`, `sentence-transformers` (CPU torch), `tiktoken`. Also available: `ipykernel` and `jupyter_client` (VS Code notebooks), Node.js 24 for page tests, and Chrome and Edge for screenshots. Check `uv pip list` (read-only) for anything else.

## 7. Output file template (use these exact headings)

Save it as `rag_learning/study/research/phase_NN_<short-name>.md`, for example `phase_05_retrieval.md`.

```markdown
# Phase N research: <phase name>

**What this is:** the research and gap audit for Phase N (<concept ids>), done <date> by <model>.
**What this is not:** lessons or code. Nothing in the course was changed.

## Summary (read this first)
- The 5 most important gaps across the phase, one line each.
- Tools to add, across the phase: one line each, with the reason.
- Decisions Yash must make: at most 5, each answerable in a word.
- Size of the build work: per concept S / M / L, and why.

## Concept <ID>: <title>
### 1. Sources checked
Book pages (verified) · repo notebooks and cells (verified) · existing course files · AE book sections · interview-repo items · external sources (numbered list with URLs).
### 2. Gap audit
| # | Idea | Used where | Taught before use? | Owner concept | Yash studied it? | Class (core / bridge / next) | How the lesson should handle it |
### 3. Quiz coverage
Key points not answerable from Short, or the needed question titles if no question file exists.
### 4. Errors found in existing material (not edited)
### 5. What the research says
The study → the result → its limits → what it means for the project, per key source. Current practice. Pitfalls. How to evaluate. Interview questions.
### 6. Lesson blueprint
The answer first (draft, 5 sentences) · The theory in one read (idea list with formulas) · Formula sheet items · Step-by-step outline (running example) · Visuals (each with what it shows) · Full-only details.
### 7. Verify notebook plan
### 8. Apply-it tool plan and real-world checklist
### 9. LLMOps notebook plan
Framework build (pieces mapped to the mechanism) · tracing (LangSmith and the local option) · dataset and evaluators · experiment against the previous version · cost/latency/token tracking · prompt and config versioning · monitoring and feedback · its place in the lifecycle · the skills used.
### 10. Tools, frameworks, libraries and LLMs
(the table from section 6, plus install lines and the keys needed)
### 11. Open questions for Yash (preferences only)

(repeat for every concept)

## Phase-level notes
Cross-concept comparisons the phase needs, ordering problems, and anything that affects other phases.

## Sources
A numbered list of every URL and paper used, each marked verified or UNVERIFIED.
```

## 8. Phases and their concepts

The concept ids come from 02. "Exists" means course files are already written; the gap audit still applies to them.

| Phase | Concepts | Exists now | Notes for the researcher |
|---|---|---|---|
| **1 · Prerequisites** | P1 LLM fundamentals · P2 IR framing · **P3 BM25 (pilot, done)** · P4 embeddings and similarity · P5 vector search · P6 retrieval evaluation basics · P7 prompting for grounded generation | full lessons, labs and FACTS for P1–P7 (written 2026-10-08, before the house style); P3 complete in the new format | Skip a new P3 audit; use P3 as the reference. P5: ANN (HNSW/IVF): `faiss-cpu` vs `hnswlib` vs NumPy exact. P1: tokenizers (`tiktoken` vs Hugging Face), Groq reasoning tokens, `max_tokens`. P6: metric definitions must match 06 (CE@k, Hit@k, MRR, nDCG). |
| **2 · Core RAG baseline → v0** | C1 parsing · C2 chunking (lesson = `07_SAMPLE_LESSON.md`) · C3 embedding and indexing with metadata · C4 dense retrieval · C5 context and generation with citations · C6 the v0 pipeline and traces · C7 structured-data RAG (no lesson yet) | lessons and labs C1–C6 | C1: compare parsers (pdfplumber, unstructured, docling, marker), but pymupdf stays pinned. Corpus T is not yet chosen (DEC-3): propose candidates, do not choose. C7: pandas vs SQL (`sqlite3`/DuckDB) vs vector search. |
| **3 · Measurement first → v0.1** | M1 building an eval set · M2 retrieval metrics harness · M3 generation metrics and LLM-as-judge · M4 experimental discipline · M5 failure analysis | none | Method source: the AI Eval book (paraphrase only). D-10: no judge runs before the end batch. Assess ragas, deepeval (`.deepeval/` exists at the repo root: check it read-only) and TruLens for fit, and say what to take or avoid. Statistics: bootstrap and paired tests (numpy/scipy). |
| **4 · Indexing and representation → v1.x** | I1 chunk size/overlap experiments · I2 structure-aware chunking · I3 semantic chunking · I4 proposition chunking · I5 contextual chunk headers / contextual retrieval · I6 document augmentation and HyPE · I-CMP granularity comparison | none | I4–I6 need LLM calls via Groq: estimate the call counts. Check Anthropic's "contextual retrieval" write-up (external). LangChain and LlamaIndex splitters for reading only. |
| **5 · Retrieval improvements → v2.x** | R1 sparse vs dense vs hybrid · R2 metadata filtering · R3 reranking · R4 diversity (MMR / Dartboard) · R5 hierarchical retrieval (RAPTOR) | R1 full lesson, short reading and questions | R3: cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`), Cohere Rerank (API cost), LLM reranking. R5: clustering (scikit-learn; UMAP optional) plus LLM summaries. |
| **6 · Query-side → v3.x** | Q1 query transformations (rewrite, step-back, decomposition) · Q2 HyDE vs HyPE | none | Groq call counts per question; caching; evaluation per question type. |
| **7 · Context construction → v4.x** | X1 context enrichment window and relevant segment extraction · X2 contextual compression · X3 context assembly (dedup, ordering, token budget, citations) | none | Lost-in-the-middle evidence (primary paper). Compression options (LLM-based, extractive, LLMLingua-style); fit with Groq. |
| **8 · Reliability and grounding → v5.x** | V1 grounded answers and citation verification · V2 relevance grading and groundedness check · V3 answerability and abstention · V4 hallucination-detection limits and judge reliability | none | NLI or cross-encoder groundedness models (local) vs an LLM judge (D-10). Abstention metrics. |
| **9 · Production readiness → v6** | D1 observability · D2 latency and cost budgets, caching · D3 regression eval in CI, index versioning, incremental re-indexing · D4 security and safety | none | Local-first: OpenTelemetry, Langfuse or Phoenix self-hosted vs a plain JSONL trace. CI without a remote (local git only): pre-commit, pytest, nox. D4: prompt injection, PII, data leakage. |
| **10 · Adaptive and corrective control flow → v7** | A1 adaptive retrieval / query routing · A2 corrective RAG · A3 Self-RAG · A4 feedback loops · A5 agentic RAG | none | Groq tool calling (check model support). LangGraph vs a plain Python loop. CRAG's web fallback is simulated (A-13). |
| **11 · Specialized (elective)** | S1 Graph RAG · S2 multimodal RAG · S3 MemoRAG | none | S1: networkx vs Microsoft GraphRAG vs LightRAG (weight, cost). S2: vision-capable models on Groq (check), and image captioning locally. S3: check the paper and whether a practical library exists. |
| **12 · Capstone** | K1 architecture defence | none | Synthesis plus system-design interview preparation (the MIT system-design guide's SPIDER framework). Corpus H is chosen later. The checklist for defending a design from your own registry evidence. |

**Big phases** (Phase 1 with 6 concepts to audit, Phase 2 with 7, Phase 4 with 7): if you can start helper agents, give each concept to one helper with sections 2–7 of this file, then merge their results into your one output file. Keep your own context for the phase summary and the cross-concept notes.

## 9. Session 13: consolidation (run after phases 1–12)

Read every `study/research/phase_*.md` and write three files:
1. **`study/research/TOOLS_AND_LIBRARIES.md`:** one master table: concept → purpose → library or model → pinned version → install line → offline? → cost → licence → fits the decisions?
   - Group it into "already installed", "add now (Phases 1–3)", "add later (by phase)" and "needs a decision".
   - Add the total extra disk size, and every API cost estimate per phase.
2. **`study/research/LLMOPS_TRACK.md`:** starting from `LLMOPS_FOUNDATION.md`, how the per-concept LLMOps notebooks join into **one** LLMOps pipeline across the course:
   - one tracing setup, LangSmith plus the local option;
   - one golden dataset, growing phase by phase;
   - evaluators added per phase;
   - a regression suite run on every change;
   - a monitoring view.

   Also list the accounts and keys needed, the cost per phase (Groq vs Claude), the order to build it, and which project skill guides each part.
3. **`study/research/GAPS_SUMMARY.md`:**
   - the top gaps per phase;
   - the errors found in 02/04/existing lessons, as one list for a later correction pass;
   - the decisions Yash must make, deduplicated, at most about 15;
   - the suggested build order, and its size per concept.

Do not edit anything else.

## 10. Before you finish

- Every cited page, cell and URL was opened; the rest is marked UNVERIFIED.
- No run of 15 or more words is copied from either book. Check by comparing your file with the extracted chapter text, then delete the extract.
- The output file follows the template in section 7.
- Only your output file was created. `git status` shows nothing else new from you, apart from the scratchpad.
- Reply to Yash in under 15 lines: the file path, the top 5 gaps, the tools to add, and the decisions they must make.
