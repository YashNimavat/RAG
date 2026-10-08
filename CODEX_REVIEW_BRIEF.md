# Review brief for Codex: RAG learning system, first stage

Paste everything below the line into Codex. Open Codex with its working directory set to `C:\Yash\New-Work\Book RAG\rag_learning`.

---

You are an independent reviewer. Another AI (Claude) produced the first stage of a RAG learning system for me. Review it critically **before** any notebooks or further lessons are built. **Do not rewrite the documents.** Produce a review report.

## What is in this folder

- `README.md` is the index.
- `01_SOURCE_INVENTORY.md`: sources inspected, the pinned repo commit, the machine environment, and the prior materials.
- `02_RAG_MASTER_LEARNING_PLAN.md`: 13 phases and 56 concept cards (IDs O1…K1), with mastery gates.
- `03_RAG_CONCEPT_DEPENDENCY_MAP.md`: pipeline placement, the prerequisite DAG, and technique families.
- `04_BOOK_TO_CODE_MAPPING.md`: the master traceability matrix and the chapter→notebook mapping.
- `05_LEARNING_AND_RETENTION_SYSTEM.md`: coaching rules, rubrics, spaced repetition, progress file formats.
- `06_RAG_PROJECT_AND_EVALUATION_PLAN.md`: the "Ask My Technical PDFs" project, v0…v8, the eval set and metrics.
- `07_SAMPLE_LESSON.md`: one complete lesson (C2 chunking, Parts A–M). It is the template for all future lessons.
- `08_GAP_ANALYSIS_AND_DECISIONS.md`: gaps, errors, 30 open decisions, risks, and the **readiness checklist (Part 7)**.
- `curriculum/CURRICULUM_BACKBONE.md`: the design spec that the documents call "BACKBONE".
- `sources/verification/`: the lab scripts and outputs behind the numbers in 07.

## Primary sources (read-only: do NOT modify them)

- **Book PDFs:** `C:\Yash\New-Work\Book RAG\RAG_Made_Simple_The_Complete_Visual_Guide\` (`chapter N.pdf`, `Appendix.pdf`, `intro.pdf`, `index.pdf`).
  - Citation `Ch4 p.3/15` means PDF page 3 of the 15-page file `chapter 4.pdf`. There are no printed page numbers.
  - You can extract a page with `pdftotext -f 3 -l 3 -layout "chapter 4.pdf" -`.
- **Repo:** `C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques`, at commit `009adba2be1bef49780ef73b6dd3c18fd24b035b`.
  - Notebook cell citations use **0-based** indices into the nbformat `cells` list.
  - `file:Lx-Ly` means line numbers at that commit.

## Your tasks

1. **Citation audit.**
   - Spot-check at least 10 book citations and at least 10 repo citations (notebook cells and `file:Lx-Ly`), taken from at least 4 different documents.
   - For each, report OK or WRONG, with the evidence.
2. **Factual claims.**
   - Verify at least 5 of the "upstream defects" claimed in 01, 04 and 08. Examples: `fusion_retrieval.ipynb` cell 17 score misalignment; `choose_chunk_size.py` crashing at chunk_size 128; the `"your_prompt_key"` no-op; `evaluation/evalute_rag.py` returning no aggregate.
   - Say which ones you confirmed by reading versus by running.
3. **Curriculum design.**
   - Challenge the ordering: evaluation in Phase 3 before any technique; agentic and graph RAG late; query-side work after retrieval.
   - Look for missing prerequisites, DAG errors (03 §2.1), and techniques introduced without a named failure.
4. **Evaluation design (06).**
   - Is span-level gold evidence sound?
   - Is the 40+6 question minimum adequate?
   - Are the metric definitions correct, and is retrieval quality kept separate from answer quality?
   - Is the judge-calibration protocol realistic?
   - Check the 10 draft seed items in 06 §6.7 against `upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf`.
5. **Sample lesson (07).**
   - Is it a good template?
   - Re-run at least 2 of its code blocks.
   - Check the boundary-probability math in D.3.
   - Say what should be cut or added.
6. **REVIEWER NOTEs and decisions.**
   - Give a verdict (accept / reject / amend) on every `REVIEWER NOTE` in 01–08.
   - Give a verdict on every decision in 08 Part 4 whose owner is "Reviewer".
7. **Length and duplication.**
   - The set is about 8,000 lines. Recommend concrete trims (section by section) that keep traceability intact.
8. **Readiness.**
   - Tick or untick every item in 08 Part 7, with a one-line justification each.
   - End with a verdict: READY / READY WITH FIXES / NOT READY.

## Constraints

- Do not edit any file. Write your report as a single Markdown file: `reviews/CODEX_REVIEW_<date>.md`.
- Do not fabricate. If you could not verify something, say so.
- Do not quote more than 15 consecutive words from the book.
- Rank findings by severity: **Blocker**, **Major**, **Minor**, **Nit**. For each finding give the file, the section, the problem, the evidence, and a suggested fix.
