"""R1: check every repo-cell, repo-line, book-page and course-file citation used in concepts/R1_hybrid_fusion.md,
study/reading/R1_hybrid_fusion.md and study/questions/R1_questions.md.

Read-only on every source. Notebook cells are 0-based; .py lines are 1-based. Book pages are 1-based PDF pages of the
split chapter files. Book phrases checked here are short (< 15 words); the lessons paraphrase. No book text is saved.
Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/R1/r1_sources.py "$B" > sources/verification/R1/out_r1_sources.txt
"""
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

ROOT = sys.argv[1]
REPO = os.path.join(ROOT, "upstream", "RAG_Techniques")
AIQ = os.path.join(ROOT, "upstream", "AI-Engineer-Interview-Questions")
BOOK = os.path.join(ROOT, "RAG_Made_Simple_The_Complete_Visual_Guide")
WS = Path(__file__).resolve().parents[3]
fails = 0
n_checks = 0


def check(ok, label):
    global fails, n_checks
    n_checks += 1
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


def norm(t):
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", t)


def git_head(path):
    return subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


check(git_head(REPO) == "009adba2be1bef49780ef73b6dd3c18fd24b035b", f"RAG_Techniques HEAD {git_head(REPO)}")
check(git_head(AIQ) == "e080df282aaf14c128ade55c177a20c38d82df1d", f"AI-Engineer-Interview-Questions HEAD {git_head(AIQ)}")

# ---------------------------------------------------------------- notebook cells (0-based)
FR = "all_rag_techniques/fusion_retrieval.ipynb"
FRL = "all_rag_techniques/fusion_retrieval_with_llamaindex.ipynb"


def cell(nb, i):
    c = json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]
    return c["cell_type"], "".join(c["source"])


CELLS = [
    (FR, 0, "markdown", ["Scores from both methods are normalized to a common scale",
                         "A weighted combination of these scores is computed (controlled by the `alpha` parameter)"]),
    (FR, 10, "code", ["FAISS.from_documents(cleaned_texts, embeddings)", "return vectorstore, cleaned_texts",
                      "chunk_size=1000, chunk_overlap=200"]),
    (FR, 14, "code", ["tokenized_docs = [doc.page_content.split() for doc in documents]", "return BM25Okapi(tokenized_docs)"]),
    (FR, 15, "code", ["bm25 = create_bm25_index(cleaned_texts)"]),
    (FR, 17, "code", ["epsilon = 1e-8",
                      'all_docs = vectorstore.similarity_search("", k=vectorstore.index.ntotal)',
                      "bm25_scores = bm25.get_scores(query.split())",
                      "vector_results = vectorstore.similarity_search_with_score(query, k=len(all_docs))",
                      "vector_scores = np.array([score for _, score in vector_results])",
                      "vector_scores = 1 - (vector_scores - np.min(vector_scores)) / (np.max(vector_scores) - np.min(vector_scores) + epsilon)",
                      "combined_scores = alpha * vector_scores + (1 - alpha) * bm25_scores",
                      "sorted_indices = np.argsort(combined_scores)[::-1]",
                      "return [all_docs[i] for i in sorted_indices[:k]]",
                      "# Step 1: Get all documents from the vectorstore"]),
    (FR, 19, "code", ['query = "What are the impacts of climate change on the environment?"', "k=5, alpha=0.5"]),
    (FRL, 3, "code", ["from llama_index.legacy.retrievers.bm25_retriever import BM25Retriever",
                      "from llama_index.core.retrievers import QueryFusionRetriever",
                      'OpenAIEmbedding(model="text-embedding-3-small", dimensions=EMBED_DIMENSION)']),
    (FRL, 8, "code", ["faiss.IndexFlatL2(EMBED_DIMENSION)"]),
    (FRL, 15, "code", ["BM25Retriever.from_defaults(", "similarity_top_k=2"]),
    (FRL, 17, "code", ["vector_retriever = index.as_retriever(similarity_top_k=2)"]),
    (FRL, 19, "code", ["QueryFusionRetriever(", "retriever_weights=[", "0.6, # vector retriever weight",
                       "0.4 # BM25 retriever weight", "num_queries=1", "mode='dist_based_score'"]),
    (FRL, 20, "markdown", ["**reciprocal_rerank**", "Since there is no normalization, this method is not suitable",
                           "**relative_score**", "**dist_based_score**", r"min\_score = mean\_score - 3 * std\_dev",
                           r"max\_score = mean\_score + 3 * std\_dev", "**simple**", "setting it to 1 disables query generation"]),
    (FRL, 22, "code", ["response = retriever.retrieve(query)"]),
]
for nb, i, kind, needles in CELLS:
    ct, src = cell(nb, i)
    check(ct == kind, f"{nb} cell {i} is a {kind} cell")
    for n in needles:
        check(n in src, f"{nb} cell {i}: {n}")
# cell 17 never re-orders the BM25 array or the vector array by document: no dict, no id lookup, no index map
_, s17 = cell(FR, 17)
check(not re.search(r"\bid\b|metadata|index_to_docstore_id|dict\(", s17), f"{FR} cell 17: no document-id alignment step")

# ---------------------------------------------------------------- runnable script lines (1-based)
SCRIPT = "all_rag_techniques_runnable_scripts/fusion_retrieval.py"
LINES = [
    (40, "vectorstore = FAISS.from_documents(cleaned_texts, embeddings)"),
    (56, "tokenized_docs = [doc.page_content.split() for doc in documents]"),
    (61, "def fusion_retrieval(vectorstore, bm25, query: str, k: int = 5, alpha: float = 0.5) -> List[Document]:"),
    (75, 'all_docs = vectorstore.similarity_search("", k=vectorstore.index.ntotal)'),
    (76, "bm25_scores = bm25.get_scores(query.split())"),
    (77, "vector_results = vectorstore.similarity_search_with_score(query, k=len(all_docs))"),
    (79, "vector_scores = np.array([score for _, score in vector_results])"),
    (80, "vector_scores = 1 - (vector_scores - np.min(vector_scores)) / (np.max(vector_scores) - np.min(vector_scores))"),
    (81, "bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) - np.min(bm25_scores))"),
    (83, "combined_scores = alpha * vector_scores + (1 - alpha) * bm25_scores"),
    (84, "sorted_indices = np.argsort(combined_scores)[::-1]"),
    (86, "return [all_docs[i] for i in sorted_indices[:k]]"),
    (100, "self.bm25 = create_bm25_index(self.cleaned_texts)"),
    (135, "parser.add_argument('--alpha', type=float, default=0.5, help='Weight for vector search vs. BM25.')"),
]
sl = open(os.path.join(REPO, SCRIPT), encoding="utf-8").read().splitlines()
for ln, needle in LINES:
    check(needle in sl[ln - 1], f"{SCRIPT}:L{ln}: {needle}")
check("epsilon" not in "\n".join(sl[74:86]), f"{SCRIPT}:L75-L86 has no epsilon")

# ---------------------------------------------------------------- repo-wide: where RRF appears (source cells and .py only)
hits = []
for p in glob.glob(os.path.join(REPO, "**", "*.ipynb"), recursive=True):
    for i, c in enumerate(json.load(open(p, encoding="utf-8"))["cells"]):
        if re.search(r"reciprocal|\bRRF\b", "".join(c["source"]), re.I):
            hits.append(f"{os.path.relpath(p, REPO)} cell {i}")
for p in glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True):
    if re.search(r"reciprocal|\bRRF\b", open(p, encoding="utf-8", errors="ignore").read(), re.I):
        hits.append(os.path.relpath(p, REPO))
hits = [h.replace(os.sep, "/") for h in hits]
check(hits == ["all_rag_techniques/fusion_retrieval_with_llamaindex.ipynb cell 20"],
      f"repo: RRF is named only in a markdown description, never implemented: {hits}")


# ---------------------------------------------------------------- book pages
def page(chapter_file, p):
    d = pymupdf.open(os.path.join(BOOK, chapter_file))
    return norm(d[p - 1].get_text()), len(d)


PAGES = [
    ("chapter 12.pdf", 1, 14, "BPA regulation 2019"),
    ("chapter 12.pdf", 1, 14, "ranks fourth"),
    ("chapter 12.pdf", 1, 14, "blind spot"),
    ("chapter 12.pdf", 2, 14, "The words are not."),
    ("chapter 12.pdf", 2, 14, "Neither retrieval method alone covers"),
    ("chapter 12.pdf", 3, 14, "Each retriever returns its own ranked list"),
    ("chapter 12.pdf", 3, 14, "normalizes the scores from both lists"),
    ("chapter 12.pdf", 3, 14, "flip to the index at the back of each book"),
    ("chapter 12.pdf", 4, 14, "complementary blind spots"),
    ("chapter 12.pdf", 5, 14, "Build Two Indexes from the Same Chunks"),
    ("chapter 12.pdf", 5, 14, "indexed twice"),
    ("chapter 12.pdf", 6, 14, "The chunks are identical."),
    ("chapter 12.pdf", 6, 14, "Query Both Retrievers in Parallel"),
    ("chapter 12.pdf", 6, 14, "tokenizes the query into individual words"),
    ("chapter 12.pdf", 7, 14, "overlap partially"),
    ("chapter 12.pdf", 7, 14, "Normalize the Scores"),
    ("chapter 12.pdf", 8, 14, "unbounded, based on term statistics"),
    ("chapter 12.pdf", 8, 14, "would dominate by sheer magnitude"),
    ("chapter 12.pdf", 8, 14, "three standard deviations below the mean"),
    ("chapter 12.pdf", 8, 14, "This method is robust"),
    ("chapter 12.pdf", 8, 14, "distorted by a single outlier score"),
    ("chapter 12.pdf", 9, 14, "represent the same thing"),
    ("chapter 12.pdf", 9, 14, "assign 0.6 to the vector"),
    ("chapter 12.pdf", 9, 14, "only that retriever's weighted score contributes"),
    ("chapter 12.pdf", 10, 14, "might weight BM25 higher"),
    ("chapter 12.pdf", 10, 14, "Normalize both score sets to 0-1 range"),
    ("chapter 12.pdf", 10, 14, "Rank all chunks by final_score"),
    ("chapter 12.pdf", 10, 14, "tokenize each chunk, build term"),
    ("chapter 12.pdf", 11, 14, "A 50/50 split gives equal say"),
    ("chapter 12.pdf", 11, 14, "60/40 or 70/30"),
    ("chapter 12.pdf", 12, 14, "measure retrieval quality at different weight settings"),
    ("chapter 12.pdf", 12, 14, "adapt the weights dynamically"),
    ("chapter 12.pdf", 12, 14, "Multi-Query Expansion"),
    ("chapter 12.pdf", 12, 14, "Overkill when"),
    ("chapter 12.pdf", 12, 14, "small enough that vector search alone"),
    ("chapter 12.pdf", 13, 14, "Latency is extremely constrained"),
    ("chapter 12.pdf", 13, 14, "Significant improvement when queries"),
    ("chapter 12.pdf", 13, 14, "the improvement in recall"),
    ("chapter 12.pdf", 14, 14, "Score normalization is essential"),
    ("chapter 12.pdf", 14, 14, "Typical configurations range from 50/50 to 70/30"),
    ("chapter 13.pdf", 5, 13, "Vector search, BM25, or the"),
    ("Appendix.pdf", 14, 23, "Best Match 25"),
    ("Appendix.pdf", 16, 23, "Fusion Retrieval Running two different retrievers"),
    ("Appendix.pdf", 17, 23, "weighted scores into a single ranked list"),
    ("Appendix.pdf", 19, 23, "Min-Max Normalization"),
    ("Appendix.pdf", 19, 23, "distorted by a single outlier"),
    ("Appendix.pdf", 21, 23, "Score Normalization"),
]
for f, p, total, phrase in PAGES:
    t, n = page(f, p)
    check(n == total and phrase in t, f"{f} p.{p}/{n}: '{phrase}'")

# Absences: across the whole book, and inside chapter 12
absent = {r"reciprocal rank fusion": [], r"\bRRF\b": [], r"rank fusion": [], r"Cormack": [], r"z-score": [],
          r"misalign": []}
ch12_absent = {r"reciprocal": [], r"\brank\w* (?:position|based)": [], r"\bclip": [], r"alignment|aligned": []}
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    d = pymupdf.open(f)
    for i, pg in enumerate(d):
        t = norm(pg.get_text())
        for pat in absent:
            if re.search(pat, t, re.I):
                absent[pat].append(f"{os.path.basename(f)} p.{i + 1}")
        if os.path.basename(f) == "chapter 12.pdf":
            for pat in ch12_absent:
                if re.search(pat, t, re.I):
                    ch12_absent[pat].append(f"p.{i + 1}")
for pat, h in absent.items():
    check(not h, f"book (all files): pattern {pat!r} occurs nowhere ({h})")
for pat, h in ch12_absent.items():
    check(not h, f"book chapter 12: pattern {pat!r} occurs nowhere ({h})")
# 'standard deviation' occurs in chapter 12 only on p.8
sd_pages = [i + 1 for i, pg in enumerate(pymupdf.open(os.path.join(BOOK, "chapter 12.pdf")))
            if "standard deviation" in norm(pg.get_text())]
check(sd_pages == [8], f"chapter 12: 'standard deviation' only on p.8 ({sd_pages})")

# ---------------------------------------------------------------- AI-Engineer-Interview-Questions (MIT)
qa = open(os.path.join(AIQ, "04-rag-and-retrieval", "questions.md"), encoding="utf-8").read()
for needle in ["### 9. What is hybrid search, and why does pure vector search fail on some queries?",
               "### 24. How does reciprocal rank fusion work, and why fuse by rank instead of by score?",
               "def rrf(rankings: list[list[str]], k: int = 60) -> list[str]:",
               "return sorted(scores, key=scores.get, reverse=True)",
               "Ranks are invariant to all of that.",
               "It's famously insensitive - nobody meaningfully tunes it.",
               "If a doc appears in the dense list only, what's its ceiling in the fused ranking?",
               "When would weighted fusion beat RRF, and what data do you need to tune it?",
               "BM25 scores zero on perfect paraphrases with no shared vocabulary",
               "A document ranked 1st contributes 1/(60+1) ≈ 0.016 per list; rank 50 contributes ≈ 0.009."]:
    check(needle in qa, f"AIQ 04-rag-and-retrieval/questions.md: {needle[:90]}")
ch17 = open(os.path.join(AIQ, "12-coding-challenges", "17_hybrid_search_and_rerank.py"), encoding="utf-8").read().splitlines()
for ln, needle in [(131, "return sorted(fused, key=lambda doc_id: (-fused[doc_id], doc_id))"),
                   (245, "lists = [[0, 1, 2, 3, 4], [4, 1, 3, 2, 0]]"),
                   (246, "assert reciprocal_rank_fusion(lists) == [1, 0, 4, 2, 3]"),
                   (247, "assert reciprocal_rank_fusion(lists, k=0)[0] == 0"),
                   (241, "assert int(np.argmax(lex + 100 * dense)) == DECOY")]:
    check(needle in ch17[ln - 1], f"AIQ 12-coding-challenges/17_hybrid_search_and_rerank.py:L{ln}: {needle}")
lic = open(os.path.join(AIQ, "LICENSE"), encoding="utf-8").read()
check("MIT License" in lic and "Copyright (c) 2026 Om" in lic, "AIQ LICENSE: MIT, Copyright (c) 2026 Om")

# ---------------------------------------------------------------- course files this lesson relies on
bank = (WS / "sources" / "coach" / "O1_diagnostic_bank.md").read_text(encoding="utf-8")
check("Dense ranks [A, B, C] and BM25 ranks [C, A, D]" in bank and "Order: A > C > B > D" in bank,
      "O1 bank Q9: rankings dense [A, B, C], BM25 [C, A, D]; key order A > C > B > D")
slog = (WS / "progress" / "session_log.md").read_text(encoding="utf-8")
check("| O1-Q09 | A | 3 | 2 |" in slog and "**A, C, B, D**" in slog,
      "session_log 2026-10-08 #1: O1-Q09 scored 2 at confidence 3; order A, C, B, D (the R1 review item)")
rq = (WS / "reviews" / "review_queue.md").read_text(encoding="utf-8")
check("R1 reviews are paused until each concept's lesson has been read" in rq,
      "review_queue (updated 2026-10-17): the R1 review is paused until the lesson is read")
md02 = (WS / "02_RAG_MASTER_LEARNING_PLAN.md").read_text(encoding="utf-8")
card = md02[md02.index("#### R1 "):md02.index("#### R2 ")]
for needle in ["Ch12 p.1–2/14 (blind spots), p.5–6/14 (two indexes), p.7–9/14 (normalisation), p.9–12/14 (weights 0.6/0.4, 50/50–70/30)",
               "The book does not cover RRF", "fusion_retrieval.py:L75-L86", "cell 19 (`dist_based_score`)",
               "cell 20 (rejects RRF on incorrect grounds", "C#33 (Cormack et al. 2009, RRF k=60)"]:
    check(needle in card, f"02 R1 card: {needle[:80]}")
md04 = (WS / "04_BOOK_TO_CODE_MAPPING.md").read_text(encoding="utf-8")
row = next(l for l in md04.splitlines() if l.startswith("| **R1**"))
for needle in ["p.4/14–p.12/14 (sketch p.10/14)", "`fusion_retrieval.ipynb cells 10-19`", "`rs/fusion_retrieval.py:L20-L116`",
               "`fusion_retrieval_with_llamaindex.ipynb cells 15-22`", "RRF absent from the book (DV-28)"]:
    check(needle in row, f"04 R1 row: {needle}")
check("DV-27" in md04 and "vector and BM25 arrays are in different document orders" in md04, "04 DV-27 (alignment bug)")
md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
v20 = md06[md06.index("#### v2.0"):md06.index("#### v2.1")]
for needle in ["RRF over dense and BM25 top-50 lists raises CE@4 on exact-term and table/numeric items",
               "`k_rrf = 60`", "Weighted score fusion is a second arm", "three arms (dense, BM25 alone, hybrid)",
               "write a unit test that fusion preserves chunk identity",
               "if the question set has no exact-term needs"]:
    check(needle in v20, f"06 v2.0 card: {needle[:80]}")
p3 = (WS / "concepts" / "P3_bm25.md").read_text(encoding="utf-8")
check("### H.2 Repo reading guide: `fusion_retrieval.ipynb` cell 17" in p3 and "the fused ranking silently becomes vector-only" in p3,
      "P3 H.2 / G.2: cell 17 with all-zero BM25 becomes vector-only (consistent with R1)")
c4f = (WS / "sources" / "verification" / "C4" / "C4_FACTS.md").read_text(encoding="utf-8")
check("`a8aa456e76ccea3b` (first_rel)" in c4f and "`78ebfed94d0021da` (D-002 ids)" in c4f,
      "C4_FACTS S9: first_rel fp a8aa456e76ccea3b and D-002 top-4 fp 78ebfed94d0021da (R1 S4/S14 reproduce both)")
ae = next((WS / "AI Eval").glob("Chapter 2 LLMs and Evaluation Basics*.md")).read_text(encoding="utf-8")
ae_sec = ae[ae.index("## **Retrieval Fundamentals**"):][:600]
check("we recommend starting with keyword search" in ae_sec, "AE Ch2 'Retrieval Fundamentals': keyword search recommended first (short phrase)")
ml = (WS / "progress" / "misconception_log.md").read_text(encoding="utf-8")
check(all(f"## MC-00{i}" in ml for i in range(1, 7)) and "## MC-007" not in ml, "misconception log: MC-001..MC-006 exist")

print(f"\n{n_checks} checks")
print("ALL PASS" if fails == 0 else f"{fails} FAIL(S)")
