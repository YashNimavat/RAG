"""P4: check every repo-cell and book-page citation in concepts/P4_embeddings_similarity.md against the files.

Read-only on both sources. Cells are 0-based. Book pages are 1-based PDF pages of the split chapter files.
Run from rag_learning/:
    uv run python sources/verification/P4/p4_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/P4/out_p4_sources.txt
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


def cell(nb, i):
    return "".join(json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]["source"])


head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check(head == "009adba2be1bef49780ef73b6dd3c18fd24b035b", f"repo HEAD {head}")

# (notebook, 0-based cell, literal substrings that must all be in that cell)
CELLS = [
    ("all_rag_techniques/dartboard.ipynb", 23,
     ["embed_documents([query])", "index.search(", "reconstruct_batch(",
      "1 - np.dot(candidate_vectors, candidate_vectors.T)", "1 - np.dot(query_embedding, candidate_vectors.T)",
      "Using 1 - cosine_similarity as distance metric"]),
    ("all_rag_techniques/json_rag.ipynb", 19, ["MODEL_NAME = 'all-MiniLM-L6-v2'", "SentenceTransformer(MODEL_NAME)",
                                               "model.encode(corpus_texts, convert_to_numpy=True"]),
    ("all_rag_techniques/json_rag.ipynb", 21, ["faiss.IndexFlatL2(embedding_dim)", "index.add(corpus_embeddings)"]),
    ("all_rag_techniques/json_rag.ipynb", 22, ["exact same loaded Sentence Transformer model", "lower is better"]),
    ("all_rag_techniques/json_rag.ipynb", 23, ["model.encode([query_text], convert_to_numpy=True)",
                                               "index.search(query_embedding, NUM_NEIGHBORS)", "Distance: {distance:.4f}"]),
    ("all_rag_techniques/local_rag_huggingface_faiss.ipynb", 10, ['EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"']),
    ("all_rag_techniques/local_rag_huggingface_faiss.ipynb", 13, ["normalize_embeddings=True", "cosine similarity"]),
    ("all_rag_techniques/local_rag_huggingface_faiss.ipynb", 14,
     ['encode_kwargs={"normalize_embeddings": True}', "Required for cosine similarity", 'embed_query("What causes climate change?")']),
    ("all_rag_techniques/local_rag_huggingface_faiss.ipynb", 16, ["FAISS.from_documents(", "embedding=embeddings"]),
    ("all_rag_techniques/graph_rag.ipynb", 12,
     ["similarity_search_with_score(doc.page_content, k=1)", "priority = 1 / similarity_score", "heapq.heappush(priority_queue"]),
    ("all_rag_techniques/reranking.ipynb", 27,
     ["CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')", "pairs = [[query, doc.page_content] for doc in initial_docs]",
      "self.cross_encoder.predict(pairs)", "reverse=True"]),
    ("all_rag_techniques/reranking.ipynb", 29, ["k=10", "rerank_top_k=5"]),
    ("all_rag_techniques/simple_csv_rag.ipynb", 12, ["faiss.IndexFlatL2("]),
]
for nb, i, needles in CELLS:
    src = cell(nb, i)
    for n in needles:
        check(n in src, f"{nb} cell {i}: {n}")
check("distance_strategy" not in cell("all_rag_techniques/local_rag_huggingface_faiss.ipynb", 16),
      "local_rag_huggingface_faiss.ipynb cell 16: no distance_strategy passed (LangChain default used)")

# helper_functions.py encode_pdf: OpenAIEmbeddings + FAISS.from_documents, no metric argument
hf = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
check(hf[47].startswith("def encode_pdf(") and "OpenAIEmbeddings()" in hf[72] and "FAISS.from_documents(cleaned_texts, embeddings)" in hf[73],
      "helper_functions.py L48 def encode_pdf; L73 OpenAIEmbeddings(); L74 FAISS.from_documents (no metric argument)")

# Repo-wide counts over code cells and .py files
files = glob.glob(os.path.join(REPO, "**", "*.ipynb"), recursive=True) + glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True)


def count(pat):
    hits = []
    for f in files:
        rel = os.path.relpath(f, REPO).replace("\\", "/")
        if f.endswith(".ipynb"):
            try:
                cells = json.load(open(f, encoding="utf-8"))["cells"]
            except Exception:
                continue
            hits += [f"{rel} c{i}" for i, c in enumerate(cells) if c["cell_type"] == "code" and re.search(pat, "".join(c["source"]))]
        else:
            hits += [f"{rel}:L{n}" for n, line in enumerate(open(f, encoding="utf-8", errors="ignore"), 1) if re.search(pat, line)]
    return hits


for pat in (r"IndexFlatL2", r"IndexFlatIP|METRIC_INNER_PRODUCT", r"distance_strategy|DistanceStrategy",
            r"normalize_embeddings|normalize_L2", r"input_type", r"CrossEncoder\("):
    h = count(pat)
    print(f"INFO repo code matches for /{pat}/: {len(h)}: {h}")
check(len(count(r"IndexFlatIP|METRIC_INNER_PRODUCT")) == 0, "repo: no inner-product FAISS index anywhere")
check(len(count(r"distance_strategy|DistanceStrategy")) == 0, "repo: no LangChain distance_strategy override anywhere")
check(len(count(r"input_type")) == 0, "repo: no embedding input_type anywhere")


def page(chapter_file, p):
    d = fitz.open(os.path.join(BOOK, chapter_file))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


# (file, 1-based page, expected page count, short phrase that must appear; every phrase < 15 words)
PAGES = [
    ("chapter 1.pdf", 5, 14, "GPS coordinates for meaning"),
    ("chapter 1.pdf", 5, 14, "close together in mathematical space"),
    ("chapter 1.pdf", 6, 14, "carbon dioxide in the atmosphere"),
    ("chapter 1.pdf", 6, 14, "Meaning Space"),
    ("chapter 1.pdf", 8, 14, "exact same process applied to the document"),
    ("chapter 12.pdf", 8, 14, "cosine similarity, bounded between -1 and 1"),
    ("chapter 13.pdf", 6, 13, "bi-encoders versus cross-encoders"),
    ("chapter 13.pdf", 6, 13, "typically using cosine similarity"),
    ("chapter 13.pdf", 6, 13, "cannot precompute anything"),
    ("chapter 13.pdf", 7, 13, "Bi-Encoder"),
    ("chapter 13.pdf", 9, 13, "Cross-encoder reranking"),
    ("chapter 6.pdf", 1, 14, "This is the asymmetry problem"),
    ("chapter 6.pdf", 2, 14, "question-shaped embedding"),
    ("chapter 11.pdf", 1, 13, "query-document asymmetry problem"),
    ("Appendix.pdf", 13, 23, "Asymmetry Problem"),
    ("Appendix.pdf", 13, 23, "Bi-Encoder"),
    ("Appendix.pdf", 15, 23, "Cosine Similarity"),
    ("Appendix.pdf", 15, 23, "(Chapters 1, 12, 13, 15)"),
    ("Appendix.pdf", 15, 23, "Cross-Encoder"),
    ("Appendix.pdf", 16, 23, "GPS coordinates of meaning"),
]
for f, p, total, phrase in PAGES:
    t, n = page(f, p)
    check(n == total and phrase in t, f"{f} p.{p}/{n}: '{phrase}'")

# Absences and first uses across the whole book
hits = {}
for pat in (r"cosine", r"dot product", r"euclidean", r"\bL2\b", r"unit (length|vector)", r"input.type", r"prefix",
            r"truncat", r"max(imum)? sequence"):
    h = []
    for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
        d = fitz.open(f)
        for k, pg in enumerate(d):
            if re.search(pat, re.sub(r"\s+", " ", pg.get_text()), re.I):
                h.append(f"{os.path.basename(f)} p.{k + 1}/{len(d)}")
    hits[pat] = h
    print(f"INFO book pages matching /{pat}/: {h}")
check(not any(x.startswith("chapter 1.pdf") for x in hits["cosine"]),
      "book: Ch1 never says 'cosine' although the glossary (App p.15/23) lists Chapter 1 for it (DV-B4)")
check(all(not hits[p] for p in (r"dot product", r"euclidean", r"\bL2\b", r"unit (length|vector)", r"input.type", r"truncat",
                                r"max(imum)? sequence")),
      "book: no 'dot product', 'Euclidean', 'L2', 'unit length/vector', 'input type', 'truncat', 'max sequence' anywhere")
print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAIL'}")
