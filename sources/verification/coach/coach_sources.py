"""Coach citation checks for sources/coach/transfer_seed_bank.md (written 2026-10-09).

Read only. No network, no API call, no .env. Nothing in upstream/ is imported or run; files are read as text
and `git rev-parse HEAD` is called on the two pinned clones.
Run from rag_learning/ (Git Bash):
    PYTHONIOENCODING=utf-8 uv run python -I sources/verification/coach/coach_sources.py "C:/Yash/New-Work/Book RAG" \
        > sources/verification/coach/out_coach_sources.txt

Sections:
  R  repo pins: HEAD commit and LICENSE copyright line of AIQ and SDG
  Q  every "verbatim, MIT" quote in the bank is an exact substring of the named pinned file, and is in the bank
  B  book pages: short phrases (each under 15 words) on the pages the bank cites
  A  AE section headings the bank cites exist (AE is read, never printed)
  C  course anchors: each cited course fact is present in the cited course file
  X  CR-13 absence checks: the seed's scenario words do not appear in the lesson file
  W  no run of 15 or more words is shared between the bank and the AE chapters or book chapters used
  S  structure of the bank: 9 seeds, each with a 'used:' line; rules; reserves marked
Output prints PASS/FAIL lines only; book and AE text is never printed beyond the short phrases checked.
"""
import glob
import os
import re
import subprocess
import sys

import pymupdf

sys.stdout.reconfigure(encoding="utf-8")   # -I ignores PYTHONIOENCODING

ROOT = sys.argv[1]
RL = os.path.join(ROOT, "rag_learning")
AIQ = os.path.join(ROOT, "upstream", "AI-Engineer-Interview-Questions")
SDG = os.path.join(ROOT, "upstream", "ai-system-design-guide")
BOOK = os.path.join(ROOT, "RAG_Made_Simple_The_Complete_Visual_Guide")
AE = os.path.join(RL, "AI Eval")
BANK = os.path.join(RL, "sources", "coach", "transfer_seed_bank.md")
N_OK = N_BAD = 0


def check(label, ok, detail=""):
    global N_OK, N_BAD
    N_OK += bool(ok)
    N_BAD += not ok
    print(f"{'PASS' if ok else 'FAIL'} {label}" + (f"  [{detail}]" if detail else ""))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def head(t):
    print(f"\n=== {t}")


bank = read(BANK)

# ---------------------------------------------------------------- R
head("R repo pins")
for name, path, commit, line in (("AIQ", AIQ, "e080df282aaf14c128ade55c177a20c38d82df1d", "Copyright (c) 2026 Om\n"),
                                  ("SDG", SDG, "ed955b27d94201b663a741284767a1136dc83e5e", "Copyright (c) 2026 Om Bharatiya\n")):
    head_sha = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    check(f"{name} HEAD is {commit[:7]}", head_sha == commit, head_sha[:12])
    lic = read(os.path.join(path, "LICENSE"))
    check(f"{name} LICENSE is MIT with '{line.strip()}'", lic.startswith("MIT License") and line in lic)
    check(f"{name} commit and copyright line named in the bank", commit[:7] in bank and line.strip() in bank)

# ---------------------------------------------------------------- Q
head("Q verbatim quotes (bank -> pinned file)")
QUOTES = [
    ("S1", AIQ, "14-company-interview-questions/harvey.md",
     "When would you put a whole contract in the context window instead of retrieving over it? Defend the answer with numbers."),
    ("S1", AIQ, "14-company-interview-questions/harvey.md",
     "Retrieval also gives you citations for free, since you know which passages were used, which matters more here than in most domains."),
    ("S2", SDG, "06-retrieval-systems/04-vector-databases.md",
     "BM25 scores depend on corpus-wide IDF statistics. In a shared collection, one large tenant's vocabulary shifts every other tenant's keyword scores, and term statistics leak across the boundary."),
    ("S2", SDG, "06-retrieval-systems/04-vector-databases.md", "Q: How do you handle multi-tenancy in a vector database?"),
    ("S3", AIQ, "04-rag-and-retrieval/questions.md",
     "Which distance metric should you use for embedding search - cosine, dot product, or Euclidean - and does the choice actually matter?"),
    ("S3", AIQ, "04-rag-and-retrieval/questions.md",
     "Cosine scores are not calibrated, and many embedders are anisotropic, so even unrelated pairs sit well above zero and pack into a narrow positive band, which means an absolute value like 0.75 tells you little on its own."),
    ("S4", AIQ, "12-coding-challenges/08_semantic_search_rag.py",
     "    def search(self, query: str, k: int = 3) -> list[tuple[int, float]]:\n"
     "        if self._matrix is None:\n"
     "            return []\n"
     "        k = min(k, len(self.docs))\n"
     "        scores = self._matrix @ self.embedder.embed(query)  # cosine == dot (unit norm)\n"
     "        top = np.argpartition(-scores, k - 1)[:k]           # O(n) select, then sort k\n"
     "        top = top[np.argsort(-scores[top])]\n"
     "        return [(int(i), float(scores[i])) for i in top]\n"),
    ("S5", AIQ, "07-evaluation-and-observability/questions.md",
     "Which retrieval metrics would you use - recall@k, MRR, nDCG - and when does each matter?"),
    ("S5", AIQ, "07-evaluation-and-observability/questions.md",
     "fraction of queries where a relevant chunk appears in the top k."),
    ("S6", AIQ, "04-rag-and-retrieval/questions.md",
     "How would you detect that a parser silently corrupted documents, at scale, without reading every page?"),
    ("S8", AIQ, "04-rag-and-retrieval/questions.md",
     "Walk me through every stage of a production RAG pipeline, from raw documents to a cited answer."),
    ("S8", AIQ, "04-rag-and-retrieval/questions.md",
     "errors compound - 90% parsing quality × 90% retrieval recall × 90% faithful generation ≈ 73% end-to-end, so you must instrument and evaluate each stage independently"),
    ("S9", AIQ, "11-ai-system-design/case-studies/07-text-to-sql-agent.md",
     "Build 'ask our data anything' for a company with a large warehouse - PMs and analysts type questions in English, the system answers with correct numbers."),
    ("S9", AIQ, "11-ai-system-design/case-studies/07-text-to-sql-agent.md",
     "for low-cardinality columns (they prevent the classic `segment = 'Enterprise'` vs `'enterprise'` filter miss)"),
    ("S9", AIQ, "11-ai-system-design/case-studies/07-text-to-sql-agent.md",
     "execution match can false-positive on degenerate results (two wrong queries both returning 0 rows) - flag empty-result matches for manual review."),
]
for sid, repo, rel, q in QUOTES:
    src = read(os.path.join(repo, rel))
    short = q.strip().splitlines()[0][:60]
    check(f"{sid} quote in {os.path.basename(repo)}/{rel}: {short!r}", q in src)
    check(f"{sid} same quote present in the bank", q in bank)
check("AIQ GLOSSARY.md has the Recall@k entry the bank names", "**Recall@k** - whether the gold chunk made the top k"
      in read(os.path.join(AIQ, "GLOSSARY.md")))
for sid, rel, heading in (("S5", "04-rag-and-retrieval/questions.md", "### 12. What does BM25 actually compute?"),
                          ("C4 reserve", "04-rag-and-retrieval/questions.md", "### 48. Break down the latency and cost budget"),
                          ("C4 reserve", "04-rag-and-retrieval/questions.md", "### 50. \"Long-context models made RAG obsolete.\""),
                          ("S1", "14-company-interview-questions/harvey.md", "### 9. When would you put a whole contract")):
    check(f"{sid}: AIQ {rel} has '{heading[:50]}'", heading in read(os.path.join(AIQ, rel)))
check("P3 reserve: AIQ 04 Q12 follow-up names short ticket titles", "very short documents like support ticket titles"
      in read(os.path.join(AIQ, "04-rag-and-retrieval/questions.md")))
check("P5 seed: search() sits at L93-L100", (lambda L: L[92].startswith("    def search(") and "for i in top]" in L[99])(
    read(os.path.join(AIQ, "12-coding-challenges/08_semantic_search_rag.py")).splitlines()))
for rel, heading in (("06-retrieval-systems/14-production-rag-at-scale.md", "## Multi-Tenant RAG Isolation"),
                     ("01-foundations/02-tokenization-deep-dive.md", "### Pattern 2: Chunking at Token Boundaries"),
                     ("00-interview-prep/01-question-bank.md", "### Q5: How would you evaluate a RAG system?")):
    check(f"SDG {rel} has '{heading}'", heading in read(os.path.join(SDG, rel)))
check("SDG Q5 states the P@5 > 0.8 target", "target Precision@5 above 0.8" in read(os.path.join(SDG, "00-interview-prep/01-question-bank.md")))
sdg_lines = read(os.path.join(SDG, "06-retrieval-systems/04-vector-databases.md")).splitlines()
check("SDG 'The hybrid-search catch' is at line 731", sdg_lines[730].startswith("**The hybrid-search catch:**"))
chunker = read(os.path.join(SDG, "01-foundations/02-tokenization-deep-dive.md"))
check("SDG Pattern 2 loop sets start = end - overlap with no break", "start = end - overlap" in chunker
      and "while start < len(tokens):" in chunker)

# ---------------------------------------------------------------- B
head("B book pages (short phrases)")


def page_text(chapter, p):
    d = pymupdf.open(os.path.join(BOOK, f"{chapter}.pdf"))
    return d.page_count, " ".join(d[p - 1].get_text().split())


for chapter, p, total, phrases in (
        ("chapter 1", 12, 14, ["Overkill when", "fit entirely in the model", "context window",
                               "will miss most of the relevant"]),
        ("chapter 22", 11, 19, ["Distracting noise is semantically similar", "the most dangerous type",
                                "fixes the total number of retrieved documents", "about fifty percent noise",
                                "sharp collapse"]),
        ("chapter 22", 12, 19, ["collapses sharply past a critical"])):
    n, t = page_text(chapter, p)
    check(f"{chapter} has {total} pages", n == total, str(n))
    for ph in phrases:
        check(f"{chapter} p.{p}/{total} contains '{ph}'", ph in t)
check("Ch22 p.11/19 names no study ('et al.' absent)", "et al" not in page_text("chapter 22", 11)[1])

# ---------------------------------------------------------------- A
head("A AE section headings (AE text not printed)")
ae_files = {os.path.basename(p): p for p in glob.glob(os.path.join(AE, "**", "*.md"), recursive=True)}
ae7 = read(next(p for n, p in ae_files.items() if n.startswith("Chapter 7 ")))
ae2 = read(next(p for n, p in ae_files.items() if n.startswith("Chapter 2 ")))
ae12 = read(next(p for n, p in ae_files.items() if n.startswith("Chapter 12 ")))
check("AE Ch7 has 'Precision@k and Recall@k'", "## **Precision@k and Recall@k**" in ae7)
sec = ae7.split("## **Precision@k and Recall@k**")[1].split("## **Mean Reciprocal Rank")[0]
check("AE Ch7 that section ranks recall over precision for the first stage", "care more about recall than precision" in sec)
check("AE Ch7 that section cites no study (no footnote link)", "learning.oreilly.com" not in sec and "et al" not in sec)
check("AE Ch7 has 'Normalized Discounted Cumulative Gain (NDCG@k)'", "## **Normalized Discounted Cumulative Gain (NDCG@k)**" in ae7)
check("AE Ch7 IDCG re-sorts the same retrieved documents", "take the same retrieved documents, re-sort them" in ae7)
check("AE Ch12 has 'Model Cascades'", "## **Model Cascades**" in ae12)
check("AE Ch12 says the highest-probability token is output", "The token with the highest probability is the one it outputs" in ae12)
check("AE Ch2 has 'Retrieval Fundamentals'", "## **Retrieval Fundamentals**" in ae2)

# ---------------------------------------------------------------- C
head("C course anchors")
ANCHORS = [
    ("concepts/P1_llm_fundamentals.md", "| **System + user, before template overhead** | **976** |", "S1 976 (P1 D.5)"),
    ("concepts/P1_llm_fundamentals.md", "### D.7 Cost from token counts", "S1 P1 D.7"),
    ("concepts/P1_llm_fundamentals.md", "| Ch1 p.12/14 | RAG is overkill when the documents fit", "S1 Ch1 p.12/14 in P1 G.1"),
    ("concepts/P1_llm_fundamentals.md", "| Whole climate PDF | 72,593 | 13,026 (**5.57**) | 12,840 (5.65)", "P1 reserve 12,840 (P1 D.3)"),
    ("concepts/P1_llm_fundamentals.md", "| 1.0 | 0.532 | 0.323 | 0.119 | 0.026 | 557 / 301 / 117 / 25 |", "P1 reserve 557 draws (P1 D.6)"),
    ("concepts/P1_llm_fundamentals.md", "| 0.25 | 0.879 |", "P1 reserve 0.879 (P1 D.6)"),
    ("sources/verification/P1/P1_FACTS.md", "| 4.0 | 0.329 / 0.290 / 0.226 / 0.155 |", "P1 reserve T = 4 (P1_FACTS S7)"),
    ("sources/verification/P1/P1_FACTS.md", "≈71 extra prompt tokens", "S1 71 (P1_FACTS §2)"),
    ("sources/verification/P1/P1_FACTS.md", "| System + user (4,659 chars) | **976** |", "S1 976 (P1_FACTS S9)"),
    ("concepts/P7_grounded_prompting.md", "### D.4 The budget with an answer reserve", "S1 P7 D.4"),
    ("concepts/P7_grounded_prompting.md", "### D.6 Lost in the middle", "S1 P7 D.6"),
    ("concepts/C5_generation_citations.md", "### B.1 \"Sources used\" that were never used", "S1 C5 B.1"),
    ("concepts/C5_generation_citations.md", "**Retrieved but not used:**", "S1 C5 D.5"),
    ("concepts/C5_generation_citations.md", "### D.7 What the check cannot see", "S1 C5 D.7"),
    ("concepts/P3_bm25.md", "avgdl over all chunks", "S2 P3 D.1"),
    ("concepts/P3_bm25.md", "floor      = epsilon × mean of idf over ALL terms", "S2 P3 D.3 floor"),
    ("concepts/P3_bm25.md", "### D.4 Saturation (k1) and length normalisation (b)", "S2 P3 D.4"),
    ("concepts/P3_bm25.md", "At dl = avgdl and f = 1, the tf part is exactly 1 for **any** k1", "P3 reserve (P3 D.4)"),
    ("concepts/P3_bm25.md", "**J2. Every score is zero on a tiny test corpus.**", "P3 reserve J2"),
    ("concepts/P4_embeddings_similarity.md", "### D.2 The three measures", "S2 P4 D.2"),
    ("concepts/C3_embedding_indexing.md", "chunk_id = f\"{doc_id}:{snapshot_id}:{params_hash}:{seq:05d}\"", "S2 C3 D.2"),
    ("concepts/C3_embedding_indexing.md", "The key: `sha256(provider|model_id|revision|input_type|preproc_version|text)`", "S2 C3 D.4"),
    ("concepts/P4_embeddings_similarity.md", "unrelated pairs −0.0859 and −0.0478", "S3 P4 D.5"),
    ("concepts/P4_embeddings_similarity.md", "Never carry a threshold from one model to another.", "S3 P4 D.5"),
    ("concepts/C4_dense_retrieval.md", "The wrong-model rank-1 score was 0.1858", "S3 C4 D.5"),
    ("sources/verification/P5/p5_measure.py", "cand = np.flatnonzero(scores >= kth)", "S4 top_k tie-aware cut"),
    ("sources/verification/P5/p5_measure.py", "order = np.lexsort((cand, -scores[cand]))", "S4 top_k (-score, id)"),
    ("concepts/P5_vector_search.md", "### D.3 Ties and determinism", "S4 P5 D.3"),
    ("concepts/P5_vector_search.md", "| 5b | Predict distinct chunks; the ×5 duplicated index |", "S4 lab Task 5b"),
    ("concepts/P5_vector_search.md", "**J2. All four retrieved chunks say the same thing.**", "S4 P5 J2"),
    ("concepts/P6_ir_metrics.md", "R@5 = 2/3 = **0.667**. Hit@1 = **0** (c5 is not relevant); Hit@5 = **1**", "S5 P6 Part F Q1"),
    ("concepts/P6_ir_metrics.md", "Recall@k    = |{i ≤ k : rel(c_i) = 1}| / (number of relevant chunks in the qrels)", "S5 P6 D.2"),
    ("concepts/P6_ir_metrics.md", "### D.7 Preview only: Complete-Evidence@k (CE@k)", "S5 P6 D.7"),
    ("concepts/P6_ir_metrics.md", "IDCG built from the **retrieved** chunks only. Correct: 0.2421 (S7)", "P6 reserve J2"),
    ("concepts/P6_ir_metrics.md", "IDCG@k = DCG@k of the ideal order of ALL relevant chunks in the qrels", "P6 reserve D.4"),
    ("progress/session_log.md", "| O1-Q04 | A | — | 0 |", "S5 O1-Q04 scored 0"),
    ("concepts/C1_document_parsing.md", "**R1** drop a line repeated on ≥ max(3, half the text pages), digits masked", "S6 rule R1 (C1 D.5)"),
    ("concepts/C1_document_parsing.md", "R1 on the book's `index.pdf` flags 5 real section titles", "S6 R1 false positives"),
    ("concepts/C1_document_parsing.md", "| Empty vs image-only page |", "S6 C1 D.4"),
    ("concepts/C1_document_parsing.md", "**C1-T-01.** A colleague's slide decks are exported to PDF.", "S6 C1-T-01 is about slide decks"),
    ("concepts/C4_dense_retrieval.md", "### D.6 Choosing k: both sides, measured (MC-005)", "S7 C4 D.6"),
    ("concepts/C4_dense_retrieval.md", "the book calls this distracting noise (Ch22 p.11/19)", "S7 C4 D.4"),
    ("concepts/C4_dense_retrieval.md", "**C4-T-01.** A hospital indexes 3,000 drug leaflets.", "S7 C4-T-01"),
    ("07_SAMPLE_LESSON.md", "## Part I — Controlled experiment (I1)", "S7 07 Part I"),
    ("07_SAMPLE_LESSON.md", "at an equal context-token budget", "S7 07 Part I equal budget"),
    ("07_SAMPLE_LESSON.md", "        if end == len(text):\n            break", "C2 reserve fixed_window_chunks break"),
    ("07_SAMPLE_LESSON.md", "**C2-A-04.**", "C2 reserve C2-A-04"),
    ("progress/misconception_log.md", "## MC-005", "S7 MC-005"),
    ("progress/misconception_log.md", "A misconception is closed only when two check items score ≥ 3 on different days, unassisted.", "S7 closing rule"),
    ("concepts/C6_v0_pipeline.md", "### D.5 Which stage failed? Walk upstream to downstream", "S8 C6 D.5"),
    ("06_RAG_PROJECT_AND_EVALUATION_PLAN.md", "**Danger zone:**", "S8 06 §7.1"),
    ("02_RAG_MASTER_LEARNING_PLAN.md", "#### C7 — Structured data RAG (CSV/JSON)", "S9 02 C7 card"),
    ("02_RAG_MASTER_LEARNING_PLAN.md", "(\"how many customers in Chile?\")", "S9 C7 card names the Chile question"),
    ("01_SOURCE_INVENTORY.md", "| 31 | Introducing Contextual Retrieval (vendor post) | Anthropic", "P6 reserve Source C #31"),
    ("05_LEARNING_AND_RETENTION_SYSTEM.md", "| CR-13 | **Novel-scenario transfer checks.**", "rules CR-13"),
    ("05_LEARNING_AND_RETENTION_SYSTEM.md", "| CR-16 | **Record learner confidence before revealing.**", "rules CR-16"),
    # added 2026-10-09 (checker fixes): the rule cites and the S5 Hit@k formula
    ("05_LEARNING_AND_RETENTION_SYSTEM.md", "| CR-02 | **Wait for an attempt.**", "rules CR-02"),
    ("05_LEARNING_AND_RETENTION_SYSTEM.md", "| CR-04 | **No full solution before an attempt plus at least one hint.**", "rules CR-04"),
    ("05_LEARNING_AND_RETENTION_SYSTEM.md", "### 2.3 Steps in detail", "rules 05 §2.3"),
    ("05_LEARNING_AND_RETENTION_SYSTEM.md", "| **1. Part A — Recovery** | 10 min | 4–8 diagnostic questions on the new concept and its prerequisites. Asked **before** any teaching", "rules 05 §2.3 step 1 Part A before teaching"),
    ("sources/EXTERNAL_RESOURCES_REVIEW_2026-10-09.md", "6. Use items only after teaching (Part L, or review from Day 14 on), never in Part A. Hide answers until after the attempt (CR-02, CR-04).", "rules review §9 item 6"),
    ("concepts/P6_ir_metrics.md", "Hit@k       = 1 if some i ≤ k has rel(c_i) = 1, else 0", "S5 P6 D.2 Hit@k"),
]
for rel, s, label in ANCHORS:
    check(f"{label}: {rel}", s in read(os.path.join(RL, rel)))
p5 = read(os.path.join(RL, "sources/verification/P5/p5_measure.py")).splitlines()
check("S4 top_k sits at p5_measure.py L44-L54", p5[43].startswith("def top_k(") and p5[53] == "    return cand[order][:k]")

# ---------------------------------------------------------------- X
head("X CR-13 absence checks (case-insensitive)")
ABSENT = [
    ("concepts/P1_llm_fundamentals.md", ["40-page", "25,000", "whole manual", "long context", "long-context"], "S1"),
    ("concepts/P3_bm25.md", ["sixth", "add a pdf", "adding a document", "new document", "another pdf", "tenant"], "S2"),
    ("concepts/P6_ir_metrics.md", ["share of queries", "fraction of queries", "a guide says"], "S5"),
    ("concepts/C1_document_parsing.md", ["300 pdf", "without reading", "at scale"], "S6"),
    ("concepts/C4_dense_retrieval.md", ["half noise", "fifty percent", "collapse", "missing evidence is worse"], "S7"),
    ("concepts/C6_v0_pipeline.md", ["9 times in 10", "0.729", "three stages", "compound"], "S8"),
]
for rel, words, sid in ABSENT:
    t = read(os.path.join(RL, rel)).lower()
    for w in words:
        check(f"{sid}: '{w}' absent from {rel}", w not in t)
check("S9: no C7 lesson file exists yet", not glob.glob(os.path.join(RL, "concepts", "C7*")))

# ---------------------------------------------------------------- W
head("W no 15-word run shared with AE or the book")


def grams(text, n=15):
    w = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower().replace("’", "'"))
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


bank_g = grams(bank)
for label, text in (("AE Ch2", ae2), ("AE Ch7", ae7), ("AE Ch12", ae12)):
    check(f"bank shares no 15-word run with {label}", not (bank_g & grams(text)), f"{len(bank_g & grams(text))} shared")
for chapter in ("chapter 1", "chapter 22"):
    d = pymupdf.open(os.path.join(BOOK, f"{chapter}.pdf"))
    text = " ".join(p.get_text() for p in d)
    check(f"bank shares no 15-word run with book {chapter}", not (bank_g & grams(text)), f"{len(bank_g & grams(text))} shared")

# ---------------------------------------------------------------- S
head("S structure of the bank")
seeds = re.findall(r"^### (S\d) · ([A-Z]\d)", bank, flags=re.M)
check("9 seeds S1-S9", [s for s, _ in seeds] == [f"S{i}" for i in range(1, 10)], str(seeds))
check("seed concepts P1 P3 P4 P5 P6 C1 C4 C6 C7", [c for _, c in seeds] == ["P1", "P3", "P4", "P5", "P6", "C1", "C4", "C6", "C7"])
check("9 'used:' lines", len(re.findall(r"^- \*\*used:\*\*", bank, flags=re.M)) == 9)
check("each seed has a Use line", len(re.findall(r"^- \*\*Use:\*\*", bank, flags=re.M)) == 9)
check("8 repo-based seeds carry 'Source text (verbatim, MIT)'", bank.count("**Source text (verbatim, MIT):**") == 8)
s7 = bank.split("### S7")[1].split("### S8")[0]
check("S7 (AE-based) has no verbatim quote", "verbatim" not in s7)
for rule in ("**one question per turn**", "**confidence (1–3) first**", "**used once**",
             "**Never write a seed into a lesson file.**", "at most **2 new items per concept**"):
    check(f"rules contain {rule}", rule in bank)
res = bank.split("## Reserves")[1].split("## How each seed")[0]
lines = [l for l in res.splitlines() if l.startswith("- **")]
check("12 reserve lines, each marked 'reserve: use only in place of a seed'",
      len(lines) == 12 and all("reserve: use only in place of a seed" in l for l in lines), str(len(lines)))
# added 2026-10-09 (checker fixes)
check("rules: Part A cite is review §9 item 6 + 05 §2.3, and CR-02/CR-04 sit on hiding the key",
      "Never ask one in Part A or before the concept is taught (review §9 item 6; 05 §2.3 step 1" in bank
      and "Hide the key until after the attempt (CR-02, CR-04)." in bank
      and "taught (CR-02, CR-04)" not in bank)
s5 = bank.split("### S5")[1].split("### S6")[0]
check("S5 key says 'guaranteed equal' and names the none-or-all case",
      "guaranteed equal only when every query has exactly one relevant chunk" in s5
      and "none or all of its relevant chunks" in s5 and "The two are equal only when" not in s5)
# DERIVED check of that S5 sentence from the P6 D.2 formulas: per query, R relevant chunks, h of them in the top k
ok_one, ok_many = True, True
for k in range(1, 11):
    for R in range(1, 8):
        for h in range(0, min(R, k) + 1):
            recall, hit = h / R, 1 if h > 0 else 0
            if R == 1:
                ok_one &= recall == hit
            else:
                ok_many &= (recall == hit) == (h == 0 or h == R)
check("S5 DERIVED: R = 1 -> Recall@k == Hit@k always; R > 1 -> equal iff h = 0 or h = R (k 1-10, R 1-7)", ok_one and ok_many)
nd = [l for l in lines if "nDCG IDCG critique" in l]
check("P6 nDCG reserve: 0–3 grade-scale claim marked UNVERIFIED", len(nd) == 1 and "0–3 grade scale (UNVERIFIED; not re-checked here)" in nd[0])
check("coach-only header", bank.startswith("# Transfer seed bank: coach-only (the learner must not open this file)"))

print(f"\nRESULT: {N_OK} PASS, {N_BAD} FAIL")
