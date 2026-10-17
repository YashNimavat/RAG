"""P3: check every repo-cell, repo-line and book-page citation in concepts/P3_bm25.md against the files.

Read-only on both sources. Cells are 0-based. Book pages are 1-based PDF pages of the split chapter files.
Book phrases checked here are short (< 15 words); the lesson paraphrases.
Run from rag_learning/:
    uv run python sources/verification/P3/p3_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/P3/out_p3_sources.txt
"""
import glob
import json
import os
import re
import subprocess
import sys

import pymupdf as fitz

REPO, BOOK = sys.argv[1], sys.argv[2]
fails = 0


def check(ok, label):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check(head == "009adba2be1bef49780ef73b6dd3c18fd24b035b", f"repo HEAD {head}")

# ---------------------------------------------------------------- notebook cells (0-based)
FR = "all_rag_techniques/fusion_retrieval.ipynb"
FRL = "all_rag_techniques/fusion_retrieval_with_llamaindex.ipynb"
CELLS = [
    (FR, 5, ["from rank_bm25 import BM25Okapi"]),
    (FR, 10, ["def encode_pdf_and_get_split_documents(path, chunk_size=1000, chunk_overlap=200)",
              "RecursiveCharacterTextSplitter(", "length_function=len", "replace_t_with_space(texts)"]),
    (FR, 14, ["def create_bm25_index(documents: List[Document]) -> BM25Okapi:", "improvement over TF-IDF",
              "Tokenize each document by splitting on whitespace", "could be improved with more sophisticated tokenization",
              "tokenized_docs = [doc.page_content.split() for doc in documents]", "return BM25Okapi(tokenized_docs)"]),
    (FR, 15, ["bm25 = create_bm25_index(cleaned_texts)"]),
    (FR, 17, ["epsilon = 1e-8", "bm25_scores = bm25.get_scores(query.split())",
              "(np.max(bm25_scores) -  np.min(bm25_scores) + epsilon)", "np.argsort(combined_scores)[::-1]"]),
    (FR, 19, ['query = "What are the impacts of climate change on the environment?"', "k=5, alpha=0.5"]),
    (FRL, 3, ["from llama_index.legacy.retrievers.bm25_retriever import BM25Retriever"]),
    (FRL, 15, ["BM25Retriever.from_defaults(", "similarity_top_k=2"]),
    ("all_rag_techniques/simple_rag.ipynb", 3, ["rank_bm25==0.2.2"]),
]
for nb, i, needles in CELLS:
    src = "".join(json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]["source"])
    for n in needles:
        check(n in src, f"{nb} cell {i}: {n}")
# the BM25 index cell has no lower-casing anywhere
src14 = "".join(json.load(open(os.path.join(REPO, FR), encoding="utf-8"))["cells"][14]["source"])
check(".lower(" not in src14, f"{FR} cell 14: no .lower() call")

# ---------------------------------------------------------------- .py lines (1-based)
LINES = [
    ("helper_functions.py", 9, "from rank_bm25 import BM25Okapi"),
    ("helper_functions.py", 248, "def bm25_retrieval(bm25: BM25Okapi, cleaned_texts: List[str], query: str, k: int = 5)"),
    ("helper_functions.py", 262, "query_tokens = query.split()"),
    ("helper_functions.py", 265, "bm25_scores = bm25.get_scores(query_tokens)"),
    ("helper_functions.py", 268, "top_k_indices = np.argsort(bm25_scores)[::-1][:k]"),
    ("helper_functions.py", 273, "return top_k_texts"),
    ("all_rag_techniques_runnable_scripts/fusion_retrieval.py", 56, "tokenized_docs = [doc.page_content.split() for doc in documents]"),
    ("all_rag_techniques_runnable_scripts/fusion_retrieval.py", 76, "bm25_scores = bm25.get_scores(query.split())"),
    ("all_rag_techniques_runnable_scripts/fusion_retrieval.py", 81,
     "bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) - np.min(bm25_scores))"),
]
for f, ln, needle in LINES:
    lines = open(os.path.join(REPO, f), encoding="utf-8").read().splitlines()
    check(needle in lines[ln - 1], f"{f}:L{ln}: {needle}")

# bm25_retrieval is defined but never called: the name occurs only in helper_functions.py (once, the def)
users = []
for path in glob.glob(os.path.join(REPO, "**", "*"), recursive=True):
    if os.path.isfile(path) and ".git" not in path.split(os.sep) and path.endswith((".py", ".ipynb", ".md")):
        if "bm25_retrieval" in open(path, encoding="utf-8", errors="ignore").read():
            users.append(os.path.relpath(path, REPO))
hf = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read()
check(users == ["helper_functions.py"] and hf.count("bm25_retrieval") == 1,
      f"bm25_retrieval occurs only in {users}, {hf.count('bm25_retrieval')} time(s): defined, never called")


# ---------------------------------------------------------------- book pages
def page(chapter_file, p):
    d = fitz.open(os.path.join(BOOK, chapter_file))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


PAGES = [
    ("chapter 12.pdf", 1, 14, "BPA regulation 2019"),
    ("chapter 12.pdf", 1, 14, "ranks fourth"),
    ("chapter 12.pdf", 2, 14, "The words are not."),
    ("chapter 12.pdf", 3, 14, "flip to the index at the back of each book"),
    ("chapter 12.pdf", 5, 14, "Best Match 25"),
    ("chapter 12.pdf", 5, 14, "does not use embeddings at all"),
    ("chapter 12.pdf", 5, 14, "BM25 scores a chunk based on three factors"),
    ("chapter 12.pdf", 5, 14, "five times scores higher than one that mentions it once"),
    ("chapter 12.pdf", 5, 14, "scores almost nothing"),
    ("chapter 12.pdf", 5, 14, "inverse document frequency"),
    ("chapter 12.pdf", 5, 14, "length normalization"),
    ("chapter 12.pdf", 6, 14, "tokenizes the query into individual words"),
    ("chapter 12.pdf", 6, 14, "Rarity"),
    ("chapter 12.pdf", 8, 14, "unbounded, based on term statistics"),
    ("chapter 12.pdf", 10, 14, "tokenize each chunk, build term statistics"),
    ("chapter 12.pdf", 10, 14, "product codes, chemical names, legal citations"),
    ("chapter 12.pdf", 14, 14, "BM25 is a keyword-matching algorithm based on term frequency"),
    ("chapter 13.pdf", 5, 13, "Vector search, BM25, or the fusion retrieval"),
    ("Appendix.pdf", 14, 23, "Best Match 25"),
    ("Appendix.pdf", 14, 23, "length normalization"),
    ("Appendix.pdf", 17, 23, "Inverse Document Frequency"),
    ("Appendix.pdf", 17, 23, "Common words score almost nothing"),
    ("Appendix.pdf", 18, 23, "Length Normalization"),
    ("Appendix.pdf", 18, 23, "match by coincidence"),
    ("Appendix.pdf", 22, 23, "Term Frequency"),
    ("Appendix.pdf", 22, 23, "More mentions of a term signal stronger relevance"),
]
for f, p, total, phrase in PAGES:
    t, n = page(f, p)
    check(n == total and phrase in t, f"{f} p.{p}/{n}: '{phrase}'")

# Absences across the whole book
absent = {r"TF-?IDF": [], r"\bk1\b": [], r"Okapi": [], r"stemm": [], r"lowercas|lower-cas": [], r"saturat": [],
          r"stop ?words?": []}
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    d = fitz.open(f)
    for i, pg in enumerate(d):
        t = pg.get_text()
        for pat in absent:
            if re.search(pat, t, re.I):
                absent[pat].append(f"{os.path.basename(f)} p.{i + 1}")
for pat, hits in absent.items():
    check(not hits, f"book: pattern {pat!r} occurs nowhere ({hits})")

# ---------------------------------------------------------------- added 2026-10-17 (study kit: short file, question file, restyle)
print("\n--- added 2026-10-17")
UP = os.path.dirname(os.path.abspath(REPO))                     # <Book RAG>/upstream
WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))   # rag_learning/
for f, p, total, phrase in [
    ("chapter 12.pdf", 2, 14, "Keyword search misses"),
    ("chapter 12.pdf", 3, 14, "The index catches what the chef"),
    ("chapter 12.pdf", 9, 14, "serving technical queries with"),
    ("chapter 12.pdf", 12, 14, "all keyword lookups (BM25 alone"),
    ("chapter 12.pdf", 12, 14, "(vector search alone suffices)"),
    ("chapter 12.pdf", 12, 14, "Overkill when"),
    ("Appendix.pdf", 9, 23, "exact method names via keyword search"),
]:
    t, n = page(f, p)
    check(n == total and phrase in t, f"{f} p.{p}/{n}: '{phrase}'")


def read(*parts):
    return open(os.path.join(*parts), encoding="utf-8").read()


AIQ = os.path.join(UP, "AI-Engineer-Interview-Questions")
h = subprocess.run(["git", "-C", AIQ, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check(h == "e080df282aaf14c128ade55c177a20c38d82df1d", f"AI-Engineer-Interview-Questions HEAD {h}")
check("Copyright (c) 2026 Om\n" in read(AIQ, "LICENSE") and "MIT License" in read(AIQ, "LICENSE"), "AIQ LICENSE: MIT, Copyright (c) 2026 Om")
q04 = read(AIQ, "04-rag-and-retrieval", "questions.md")
q12 = q04[q04.index("### 12. "):q04.index("### 13. ")]
for needle in ["### 12. What does BM25 actually compute? Walk me through the formula's moving parts.",
               "BM25 pushes TF through `tf / (tf + k1 * (...))`", "20 to 21 barely registers",
               "`k1` (typically ~1.2 to 2.0)", "**Length normalization** divides by document length",
               "`b=0` disables it, `b=1` normalizes fully.", "BM25 is purely lexical", "depends heavily on the analyzer"]:
    check(needle in q12, f"AIQ 04 Q12: {needle[:70]}")
check("log(" not in q12 and "ln(" not in q12 and "(k1 + 1)" not in q12 and "(k1+1)" not in q12,
      "AIQ 04 Q12 gives no idf formula and no (k1 + 1) factor (P3-R-05 corrections 1 and 3)")
ae = next(iter(glob.glob(os.path.join(WS, "AI Eval", "Chapter 2 LLMs and Evaluation Basics*.md"))), None)
ae_t = read(ae) if ae else ""
check("## **Retrieval Fundamentals**" in ae_t and "we recommend starting with keyword search" in
      ae_t[ae_t.index("## **Retrieval Fundamentals**"):][:600] if ae_t else False,
      "AE Ch2 'Retrieval Fundamentals': keyword search recommended first (short phrase; paraphrased in P3 B.3)")
r1f = read(WS, "sources", "verification", "R1", "R1_FACTS.md")
for needle in ["| `IPCC` | seq 1, page 1 | 3 | 1 | none | 1 | 1 |",
               "| `What does BECCS stand for?` | seq 88, page 30 | 4 | 1 | none | 1 | 1 |",
               "| `methane CH4` | seq 2, page 1 | 4 | 1 | 2 | 1 | 1 |",
               "| `Kyoto Protocol 1997` | seq 69, page 24 | 1 | 1 | 1 | 1 | 1 |",
               "| `limit warming to 1.5 degrees` | seq 27, 68 | 4 | 1 | 1 | 2 | 1 |",
               "| dense | 8/8 | 8/8 | 0.708 | 3, 3, 1, 1, 1, 1, 2, 2",
               "| bm25 (`tok_norm`) | 8/8 | 8/8 | 0.938 | 1, 1, 1, 1, 1, 2, 1, 1 |",
               "| bm25 (`split()`) | 8/8 | 8/8 | 0.875 | 1, 2, 1, 1, 1, 2, 1, 1 |",
               "BM25 seq 64 13.6205, seq 21 9.2298", "(`panels` idf 4.1641)",
               "D-009 dense 0.3099 → 1.0, BM25 6.9559 → 1.0; D-010 dense 0.5196 → 1.0, BM25 13.2576 → 1.0",
               "avgdl 111.23, vocab 1,769", "repo-style (with epsilon) returns [89, 50, 48, 49, 81]", "NaN 97/97",
               "**P3 H.2 answer 4**: \"vector-only\" holds for aligned arrays"]:
    check(needle in r1f, f"R1_FACTS: {needle[:80]}")
md06 = read(WS, "06_RAG_PROJECT_AND_EVALUATION_PLAN.md")
s62 = md06[md06.index("### 6.2 Categories and target counts"):md06.index("### 6.3")]
check("| exact-term (acronyms, names, numbers) |" in s62, "06 §6.2: the exact-term category")
s42 = md06[md06.index("### 4.2 Version cards"):md06.index("### 4.3")]
check("three arms (dense, BM25 alone, hybrid)" in s42, "06 §4.2 v2.0 card: three arms (dense, BM25 alone, hybrid)")
md02 = read(WS, "02_RAG_MASTER_LEARNING_PLAN.md")
card = md02[md02.index("#### P3 — "):md02.index("#### P4 — ")]
check("Ch12 p.5–6/14" in card and not any(p in card for p in ("p.1–2/14", "p.8/14", "p.10/14", "p.12/14", "p.14/14")),
      "02 P3 card: book pages Ch12 p.5–6/14 only (P3 G.3 item 5)")
row04 = next(l for l in read(WS, "04_BOOK_TO_CODE_MAPPING.md").splitlines() if l.startswith("| **P3** "))
check("`fusion_retrieval.ipynb cells 14-15`" in row04 and "cell 17" not in row04 and "p.5/14–p.6/14" in row04
      and not any(p in row04 for p in ("p.8/14", "p.10/14", "p.12/14", "App")), "04 P3 row: cells 14-15 only; book p.5–6/14 only (P3 G.3 items 1-2)")

print("\nALL PASS" if fails == 0 else f"\n{fails} FAIL(S)")
