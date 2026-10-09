"""P5: check every repo-cell, book-page and library-source citation in concepts/P5_vector_search.md.

Read-only on all sources. Cells are 0-based. Book pages are 1-based PDF pages of the split chapter files.
The third argument is OPTIONAL: a site-packages folder OUTSIDE the project env that holds langchain_community
and langchain_core (the learner's older venv). The files are only read as text; nothing is imported or installed.

Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P5/p5_sources.py "$B/upstream/RAG_Techniques" \
        "$B/RAG_Made_Simple_The_Complete_Visual_Guide" "C:/Yash/New-Work/RAG/RAG_Techniques-main/venv/Lib/site-packages"
Saved output: sources/verification/P5/out_p5_sources.txt
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

import pymupdf as fitz

REPO, BOOK = sys.argv[1], sys.argv[2]
SITE = sys.argv[3] if len(sys.argv) > 3 else None
fails = 0


def check(ok, label):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check(head == "009adba2be1bef49780ef73b6dd3c18fd24b035b", f"repo HEAD {head}")

# ---------------------------------------------------------------- repo: helper_functions.py lines (1-based)
hf = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
for ln, needle in ((4, "from langchain_community.vectorstores import FAISS"),
                   (48, "def encode_pdf(path, chunk_size=1000, chunk_overlap=200):"),
                   (73, "embeddings = OpenAIEmbeddings()"),
                   (74, "vectorstore = FAISS.from_documents(cleaned_texts, embeddings)")):
    check(needle in hf[ln - 1], f"helper_functions.py L{ln}: {needle}")

# ---------------------------------------------------------------- repo: notebook cells (0-based)
CELLS = [
    ("all_rag_techniques/simple_rag.ipynb", 10, ["FAISS.from_documents(cleaned_texts, embeddings)", "chunk_size=1000"]),
    ("all_rag_techniques/simple_rag.ipynb", 13, ['as_retriever(search_kwargs={"k": 2})']),
    ("all_rag_techniques/simple_csv_rag.ipynb", 12, ["faiss.IndexFlatL2(", "InMemoryDocstore()", "index_to_docstore_id={}"]),
    ("all_rag_techniques/simple_csv_rag.ipynb", 16, ["retriever = vector_store.as_retriever()"]),
    ("all_rag_techniques/json_rag.ipynb", 17, ['corpus_metadata.append({"original_index": i, "data": item})']),
    ("all_rag_techniques/json_rag.ipynb", 21, ["faiss.IndexFlatL2(embedding_dim)", "index.add(corpus_embeddings)"]),
    ("all_rag_techniques/json_rag.ipynb", 23, ["NUM_NEIGHBORS = 5", "index.search(query_embedding, NUM_NEIGHBORS)"]),
    ("all_rag_techniques/dartboard.ipynb", 9, ["documents=documents*5", "FAISS.from_documents(cleaned_texts, embeddings)"]),
    ("all_rag_techniques/dartboard.ipynb", 13, ["index_to_docstore_id[idx]", "docstore.search(docstore_id)",
                                                "embed_documents([query])", "index.search(np.array(q_vec),k=k)"]),
    ("all_rag_techniques/dartboard.ipynb", 23, ["index.search(", "k=num_results * oversampling_factor",
                                                "reconstruct_batch(candidate_indices[0])",
                                                "1 - np.dot(candidate_vectors, candidate_vectors.T)"]),
    ("all_rag_techniques/multi_faceted_filtering.ipynb", 12, ["similarity_search_with_relevance_scores(query, k=10)"]),
    ("all_rag_techniques/multi_faceted_filtering.ipynb", 14, ["def apply_metadata_filter(",
                                                             'apply_metadata_filter(results, {"country": "Chile"})']),
]
for nb, i, needles in CELLS:
    cell = json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]
    src = "".join(cell["source"])
    for n in needles:
        check(cell["cell_type"] == "code" and n in src, f"{nb} cell {i}: {n}")

# ---------------------------------------------------------------- repo-wide scans
code_l2, absent, kvals = [], {}, []
BAD = ["IndexFlatIP", "IndexHNSW", "IndexIVF", "DistanceStrategy", "normalize_L2", "hnswlib"]
for f in sorted(glob.glob(os.path.join(REPO, "**", "*.ipynb"), recursive=True)):
    rel = os.path.relpath(f, REPO).replace("\\", "/")
    for i, c in enumerate(json.load(open(f, encoding="utf-8"))["cells"]):
        s = "".join(c["source"])
        if c["cell_type"] == "code" and "faiss.IndexFlatL2(" in s:
            code_l2.append(f"{rel} cell {i}")
        for b in BAD:
            if b in s:
                absent.setdefault(b, []).append(f"{rel} cell {i}")
        if c["cell_type"] == "code":
            for m in re.finditer(r"""search_kwargs\s*=\s*\{[^}]*['"]k['"]\s*:\s*(\w+)|similarity_top_k\s*=\s*(\w+)""", s):
                kvals.append((rel, i, m.group(1) or m.group(2)))
for f in sorted(glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True)):
    s = open(f, encoding="utf-8", errors="replace").read()
    for b in BAD:
        if b in s:
            absent.setdefault(b, []).append(os.path.relpath(f, REPO))
print(f"INFO code cells that build faiss.IndexFlatL2 ({len(code_l2)}): {code_l2}")
check(len(code_l2) == 8, "8 notebook code cells build faiss.IndexFlatL2")
check(not absent, f"no IndexFlatIP / HNSW / IVF / DistanceStrategy / normalize_L2 / hnswlib anywhere in the repo: {absent or 'none'}")
print(f"INFO k settings in code cells ({len(kvals)}):")
for rel, i, v in kvals:
    print(f"     {rel} cell {i}: k = {v}")
print("INFO distinct literal k values:", sorted({v for _, _, v in kvals if v.isdigit()}, key=int))


# ---------------------------------------------------------------- book pages
def page(chapter_file, p):
    d = fitz.open(os.path.join(BOOK, chapter_file))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


PAGES = [  # (file, 1-based page, page count, phrase; every phrase < 15 words)
    ("chapter 1.pdf", 6, 14, "Store in a Vector Database"),
    ("chapter 1.pdf", 6, 14, "Facebook AI Similarity Search"),
    ("chapter 1.pdf", 6, 14, "even with millions of entries"),
    ("chapter 1.pdf", 7, 14, "Store all vectors in a vector store for fast similarity"),
    ("chapter 1.pdf", 8, 14, "exact same process"),
    ("chapter 1.pdf", 8, 14, "top 2 to 5 most similar chunks"),
    ("chapter 1.pdf", 9, 14, "three nearest chunks are highlighted"),
    ("chapter 1.pdf", 10, 14, "Search vector store for top-K nearest chunk vectors"),
    ("chapter 1.pdf", 13, 14, "one vector search"),
    ("Appendix.pdf", 15, 23, "Cosine Similarity A mathematical measure"),
    ("Appendix.pdf", 16, 23, "FAISS Facebook AI Similarity Search, a vector database"),
    ("Appendix.pdf", 21, 23, "Similarity Search The process of finding the stored vectors closest"),
    ("Appendix.pdf", 22, 23, "Top-K Retrieval The standard retrieval approach"),
    ("Appendix.pdf", 22, 23, "Vector Database / Vector Store A specialized database"),
    ("chapter 12.pdf", 8, 14, "bounded between -1 and 1"),
    ("chapter 13.pdf", 6, 13, "can be precomputed and stored"),
    ("chapter 15.pdf", 1, 12, "redundancy problem"),
    ("chapter 15.pdf", 1, 12, "essentially the same paragraph repeated"),
    ("chapter 11.pdf", 6, 13, "carries a pointer back to the parent chunk"),
    ("chapter 14.pdf", 7, 13, "filtering by section identifiers"),
    ("chapter 15.pdf", 10, 12, "Standard top-K is simpler and faster"),
]
for f, p, total, phrase in PAGES:
    t, n = page(f, p)
    check(n == total and phrase in t and len(phrase.split()) < 15, f"Book {f} p.{p}/{n}: '{phrase}'")

hits = {}
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    for i, pg in enumerate(fitz.open(f)):
        t = re.sub(r"\s+", " ", pg.get_text())
        for term in ("HNSW", "approximate nearest", "IVF", "argpartition", "inverted file", "brute force", "exhaustive"):
            if term.lower() in t.lower():
                hits.setdefault(term, []).append(f"{os.path.basename(f)} p.{i+1}")
check(not any(k in hits for k in ("HNSW", "approximate nearest", "IVF", "argpartition", "inverted file")),
      f"book never mentions HNSW / approximate nearest / IVF / argpartition / inverted file (other hits: {hits})")

# ---------------------------------------------------------------- library source (outside the project env; read as text)
if SITE and os.path.isdir(SITE):
    dist = sorted(d for d in os.listdir(SITE) if re.match(r"(langchain_community|langchain_core|faiss_cpu)-.*dist-info", d))
    print("INFO library versions in", SITE, ":", dist)
    fa = os.path.join(SITE, "langchain_community", "vectorstores", "faiss.py")
    ba = os.path.join(SITE, "langchain_core", "vectorstores", "base.py")
    for path in (fa, ba):
        print(f"INFO sha256 {os.path.relpath(path, SITE)} = {hashlib.sha256(open(path, 'rb').read()).hexdigest()}")
    fl = open(fa, encoding="utf-8").read().splitlines()
    bl = open(ba, encoding="utf-8").read().splitlines()

    def at(lines, ln, needle, label):
        check(needle in lines[ln - 1], f"{label} L{ln}: {needle}")

    at(fl, 214, "distance_strategy: DistanceStrategy = DistanceStrategy.EUCLIDEAN_DISTANCE", "faiss.py __init__")
    at(fl, 213, "normalize_L2: bool = False", "faiss.py __init__")
    at(fl, 993, "distance_strategy: DistanceStrategy = DistanceStrategy.EUCLIDEAN_DISTANCE", "faiss.py __from")
    at(fl, 998, "index = faiss.IndexFlatIP(len(embeddings[0]))", "faiss.py __from (only for MAX_INNER_PRODUCT)")
    at(fl, 1000, "# Default to L2, currently other metric types not initialized.", "faiss.py __from")
    at(fl, 1001, "index = faiss.IndexFlatL2(len(embeddings[0]))", "faiss.py __from")
    at(fl, 390, "k: int = 4,", "faiss.py similarity_search_with_score_by_vector")
    at(fl, 392, "fetch_k: int = 20,", "faiss.py similarity_search_with_score_by_vector")
    at(fl, 417, "scores, indices = self.index.search(vector, k if filter is None else fetch_k)", "faiss.py (post-filter)")
    at(fl, 450, "return docs[:k]", "faiss.py")
    at(fl, 1272, "return self._euclidean_relevance_score_fn", "faiss.py _select_relevance_score_fn")
    at(bl, 362, "self, query: str, k: int = 4, **kwargs: Any", "langchain_core base.py similarity_search")
    at(fl, 626, "k: int = 4,", "faiss.py FAISS.similarity_search")
    at(bl, 1043, "kwargs_ = self.search_kwargs | kwargs", "langchain_core base.py VectorStoreRetriever._get_relevant_documents")
    at(bl, 1045, "docs = self.vectorstore.similarity_search(query, **kwargs_)", "langchain_core base.py VectorStoreRetriever._get_relevant_documents")
    at(bl, 970, 'search_type: str = "similarity"', "langchain_core base.py VectorStoreRetriever")
    at(bl, 973, "search_kwargs: dict = Field(default_factory=dict)", "langchain_core base.py VectorStoreRetriever")
    at(bl, 388, "return 1.0 - distance / math.sqrt(2)", "langchain_core base.py _euclidean_relevance_score_fn")
    at(bl, 385, "# This function converts the Euclidean norm of normalized embeddings", "langchain_core base.py")
else:
    print("INFO no site-packages folder given: LangChain defaults stay UNVERIFIED")

print("ALL PASS" if fails == 0 else f"{fails} FAIL")
