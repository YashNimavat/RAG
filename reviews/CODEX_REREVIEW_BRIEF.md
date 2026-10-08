# Re-review brief for Codex: P0/P1 corrections

Paste everything below the line into Codex, with its working directory set to `C:\Yash\New-Work\Book RAG\rag_learning`.

---

You reviewed this workspace on 2026-10-08 (`reviews/CODEX_REVIEW_2026-10-08.md`, NOT READY, 84/100). Claude has since applied corrections for your **P0 and P1 findings only**: B-01 and M-01 to M-07. Re-review **only those corrections**. Do not edit any file. Do not re-review minor findings, the trim proposal or untouched content.

Read first:
- `reviews/CORRECTIONS_LOG_2026-10-08.md`: one section per finding. Each gives how the finding was re-verified, the correction, the files and sections changed, and the acceptance evidence.
- `reviews/CORRECTIONS_SPEC_2026-10-08.md`: the canonical contracts that were applied.

Changed sections carry the marker `Revised 2026-10-08 (Codex <ID>)`. Find them with: `grep -n "Revised 2026-10-08" *.md curriculum/*.md`.

Primary sources (read-only):
- Climate PDF: `C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques\data\Understanding_Climate_Change.pdf`
- Repo: pinned at commit `009adba2be1bef49780ef73b6dd3c18fd24b035b`.

Tasks:
1. **For each finding (B-01, M-01 to M-07), check your own acceptance criteria from §3 of your report against the edited text.** Verdict per finding: RESOLVED / PARTIALLY RESOLVED / NOT RESOLVED, with evidence (file + section).
2. **Re-run the executable checks:**
   - `python -I sources/verification/corrections/contracts_check.py "<climate PDF path>"`. It should report 80 passed, 0 failed.
   - The tests in `07_SAMPLE_LESSON.md` H.3. Extract the H.1 and H.3 blocks and run pytest; 13 tests are expected to pass.
   - Inspect at least two checks in the script to confirm they test what they claim.
3. **Spot-check the corrected seed spans** (06 §6.7: D-004 p.23 [1437,1566); D-007 p.10 [137,339) and p.29 [963,1106)) for semantic sufficiency.
4. **Re-evaluate the readiness items in 08 Part 7**, now staged into approval gates A, B and C. State whether **approval gate A (design approval)** can be granted, or exactly what blocks it.
5. **Flag any new problem the corrections introduced:** a contradiction between files, a broken contract or a regression.

Write a single report to `reviews/CODEX_REREVIEW_<date>.md` with severities Blocker/Major/Minor/Nit. End with a verdict: **GATE A GRANTED** / **GATE A GRANTED WITH FIXES** / **NOT GRANTED**.
