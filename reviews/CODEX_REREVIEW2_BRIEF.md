# Re-review 2 brief for Codex: R-01 to R-07

Paste everything below the line into Codex, with its working directory set to `C:\Yash\New-Work\Book RAG\rag_learning`.

---

Your re-review (`reviews/CODEX_REREVIEW_2026-10-08.md`) did **not grant Gate A**. It left four findings partially resolved and raised R-01 to R-07. Claude has since applied round-2 corrections. Re-review **only** those, plus the readiness items they unblock. Do not edit any file except your report.

Read first:
- `reviews/CORRECTIONS_LOG_2026-10-08.md`, section **"Round 2"**: one entry per R-finding (problem, fix, files and sections, acceptance evidence) and the decisions recorded before Gate A.
- `reviews/CORRECTIONS_SPEC_R2_2026-10-08.md`: the contracts applied.

Changed sections carry `Revised 2026-10-08 (Codex re-review R-0x)`. Find them with: `grep -n "Codex re-review R-" *.md curriculum/*.md reviews/CORRECTIONS_SPEC_2026-10-08.md`.

Tasks:
1. **Verdict per finding** (R-01 to R-07): RESOLVED / PARTIALLY / NOT RESOLVED, against the "Correction" and "Acceptance" text in your re-review §3, with file and section evidence.
2. **Re-run the checks:**
   - `python -I sources/verification/corrections/contracts_check.py "C:\Yash\New-Work\Book RAG\upstream\RAG_Techniques\data\Understanding_Climate_Change.pdf"`. Expect 142 passed, 0 failed.
   - Repeat your own negative probes from the re-review: the wrong manifest digest, the shifted `["abc","def"]` page table, exposed-only I-CMP, shuffled qid metadata, and the κ = −1 case.
   - Re-run the 07 H.1 + H.3 pytest (13 expected).
3. **Check that the documented `snapshot_id` recipe** (06 §5.3) reproduces `ea07572562ac` for Corpus D (PyMuPDF 1.26.7, options `{}`, cleaning `none`).
4. **Re-evaluate 08 Part 7 Gate A items**, especially C-1, DEC-1a, DEC-1b, V-1, V-4, P-1 and P-2. State whether **Gate A (design approval)** can now be granted.
5. **Flag anything new the round-2 corrections broke.**

Write your report to `reviews/CODEX_REREVIEW2_<date>.md` with severities Blocker/Major/Minor/Nit. End with **GATE A GRANTED** / **GRANTED WITH FIXES** / **NOT GRANTED**.
