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

print("\nALL PASS" if fails == 0 else f"\n{fails} FAIL(S)")
