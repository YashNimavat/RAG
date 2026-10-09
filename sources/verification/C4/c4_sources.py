"""C4 citation checks: every repo cell (0-based), helper line, library line and book page cited in
concepts/C4_dense_retrieval.md is opened and checked for the content the lesson attributes to it.

Read only. No network, no API call, no .env. Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C4/c4_sources.py "$B/upstream/RAG_Techniques" \
        "$B/RAG_Made_Simple_The_Complete_Visual_Guide" "C:/Yash/New-Work/RAG/RAG_Techniques-main/venv/Lib/site-packages" \
        > sources/verification/C4/out_c4_sources.txt
The third argument is the learner's OLDER venv (outside the project env), read as text only.
"""
import glob
import json
import os
import re
import subprocess
import sys

import pymupdf

REPO, BOOK, SP = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else None)
N_OK = N_BAD = 0


def check(label, ok, detail=""):
    global N_OK, N_BAD
    N_OK += bool(ok)
    N_BAD += not ok
    print(f"{'PASS' if ok else 'FAIL'} {label}" + (f"  [{detail}]" if detail else ""))


def norm(s):
    return " ".join(s.split())


def cell(nb, i):
    c = json.load(open(os.path.join(REPO, "all_rag_techniques", nb), encoding="utf-8"))["cells"]
    return c[i]["cell_type"], "".join(c[i]["source"])


def ncells(nb):
    return len(json.load(open(os.path.join(REPO, "all_rag_techniques", nb), encoding="utf-8"))["cells"])


print("=== repo")
head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check("repo HEAD is the pinned commit", head == "009adba2be1bef49780ef73b6dd3c18fd24b035b", head)

t, s = cell("simple_rag.ipynb", 13)
check("simple_rag.ipynb cell 13: as_retriever(search_kwargs={'k': 2})", t == "code" and 'search_kwargs={"k": 2}' in s)
t, s = cell("simple_rag.ipynb", 15)
check("simple_rag.ipynb cell 15: retrieve_context_per_question + show_context; no score in the cell",
      t == "code" and "retrieve_context_per_question(test_query, chunks_query_retriever)" in s
      and "show_context(context)" in s and "score" not in s.lower())
t, s = cell("simple_rag.ipynb", 10)
check("simple_rag.ipynb cell 10: encode_pdf -> FAISS.from_documents (the store C4 reads from)",
      "FAISS.from_documents(cleaned_texts, embeddings)" in s)

H = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
L = lambda n: H[n - 1]  # noqa: E731  (1-based line)
check("helper_functions.py L129 def retrieve_context_per_question", L(129).startswith("def retrieve_context_per_question("))
check("helper_functions.py L131-L140 docstring promises 'a tuple' with 'unique URLs'",
      any("A tuple containing" in L(n) for n in range(131, 141)) and any("unique URLs" in L(n) for n in range(131, 141)))
check("helper_functions.py L143 calls get_relevant_documents", "chunks_query_retriever.get_relevant_documents(question)" in L(143))
check("helper_functions.py L147 keeps only page_content (scores and metadata dropped)",
      L(147).strip() == "context = [doc.page_content for doc in docs]")
check("helper_functions.py L149 returns the list only (no tuple, no URLs)", L(149).strip() == "return context")
check("helper_functions.py L79/L117 encode_from_string sets a constant relevance_score = 1.0",
      L(79).startswith("def encode_from_string(") and L(117).strip() == "chunk.metadata['relevance_score'] = 1.0")
check("helper_functions.py L208-L220 show_context prints 'Context i:' and the text only",
      L(208).startswith("def show_context(") and 'print(f"Context {i + 1}:")' in "\n".join(H[207:221])
      and "score" not in "\n".join(H[207:221]).lower())

t, s = cell("json_rag.ipynb", 22)
check("json_rag.ipynb cell 22 (markdown): same model / same embedding space; L2 distance, lower is better",
      t == "markdown" and "exact same loaded Sentence Transformer model" in s and "lower is better" in s and "L2 distance" in s)
t, s = cell("json_rag.ipynb", 23)
check("json_rag.ipynb cell 23: model.encode([query_text]) (no normalize), index.search(..., NUM_NEIGHBORS=5), prints Distance",
      t == "code" and "model.encode([query_text], convert_to_numpy=True)" in s and "normalize" not in s
      and "NUM_NEIGHBORS = 5" in s and "index.search(query_embedding, NUM_NEIGHBORS)" in s and 'Distance: {distance:.4f}' in s)
t, s = cell("json_rag.ipynb", 21)
check("json_rag.ipynb cell 21: IndexFlatL2", "IndexFlatL2" in s)

t, s = cell("multi_faceted_filtering.ipynb", 10)
check("multi_faceted_filtering.ipynb cell 10: all-MiniLM-L6-v2 + Chroma.from_documents",
      'HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")' in s and "Chroma.from_documents" in s)
t, s = cell("multi_faceted_filtering.ipynb", 12)
check("multi_faceted_filtering.ipynb cell 12: similarity_search_with_relevance_scores(query, k=10), prints score",
      "similarity_search_with_relevance_scores(query, k=10)" in s and 'print(f"{score:.3f}' in s)

t, s = cell("dartboard.ipynb", 13)
check("dartboard.ipynb cell 13: the query is embedded with embed_documents (document side)",
      "embed_documents" in s and "embed_query" not in s)

# where does the repo ever expose a retrieval score? (code cells calling a score-returning API)
api = re.compile(r"similarity_search_with_score|similarity_search_with_relevance_scores|"
                 r"similarity_search_by_vector_with_relevance_scores|\.search\(")
found = {}
for p in sorted(glob.glob(os.path.join(REPO, "all_rag_techniques", "*.ipynb"))):
    cs = json.load(open(p, encoding="utf-8"))["cells"]
    hits = [i for i, c in enumerate(cs) if c["cell_type"] == "code" and api.search("".join(c["source"]))]
    if hits:
        found[os.path.basename(p)] = hits
n_nb = len(glob.glob(os.path.join(REPO, "all_rag_techniques", "*.ipynb")))
print(f"INFO notebooks with a code cell calling a score-returning search API: {len(found)} of {n_nb}: {found}")
check("simple_rag.ipynb never calls a score-returning API", "simple_rag.ipynb" not in found)
grd = [os.path.basename(p) for p in glob.glob(os.path.join(REPO, "all_rag_techniques", "*.ipynb"))
       if "get_relevant_documents" in open(p, encoding="utf-8").read()]
print(f"INFO notebooks whose source mentions get_relevant_documents: {len(grd)}: {sorted(grd)}")
kv = []
for p in glob.glob(os.path.join(REPO, "all_rag_techniques", "*.ipynb")):
    for c in json.load(open(p, encoding="utf-8"))["cells"]:
        if c["cell_type"] == "code":
            kv += re.findall(r'["\']k["\']\s*:\s*(\d+)', "".join(c["source"]))
print(f"INFO literal search_kwargs k values across notebooks: {sorted(set(map(int, kv)))} (n={len(kv)})")

print("\n=== library source (older venv, read as text, not run)")
if SP and os.path.isdir(SP):
    rp = os.path.join(SP, "langchain_core", "retrievers.py")
    src = open(rp, encoding="utf-8").read()
    ver = [d for d in os.listdir(SP) if d.startswith("langchain_core-")]
    print("INFO", ver)
    check("langchain_core retrievers.py has no public 'def get_relevant_documents'",
          re.search(r"^\s*def get_relevant_documents\(", src, re.M) is None)
    check("langchain_core retrievers.py defines invoke(...) and the private _get_relevant_documents",
          re.search(r"^\s*def invoke\(", src, re.M) is not None and "def _get_relevant_documents" in src)
else:
    print("SKIP library checks (no site-packages path given): UNVERIFIED")

print("\n=== cohere SDK in the project env (signature inspected, never called)")
import inspect  # noqa: E402

import cohere  # noqa: E402

sig = str(inspect.signature(cohere.ClientV2.embed))
print("INFO cohere", cohere.__version__)
check("cohere ClientV2.embed takes input_type with 'search_query' and 'search_document'",
      "input_type" in sig and "'search_query'" in sig and "'search_document'" in sig)

print("\n=== book (PyMuPDF text, whitespace-normalised; each phrase must be on the cited page)")
BOOKCHECKS = [
    ("chapter 1", 8, ["exact same process", "same \u201cmeaning space\u201d", "top 2 to 5"]),
    ("chapter 1", 9, ["three nearest chunks"]),
    ("chapter 1", 10, ["top-K nearest chunk vectors", "Retrieve the corresponding text chunks"]),
    ("chapter 1", 12, ["small, fixed number of chunks", "retrieves only two or three chunks"]),
    ("chapter 6", 1, ["asymmetry problem", "surprisingly far apart"]),
    ("Appendix", 13, ["Asymmetry Problem"]),
    ("chapter 11", 2, ["less relevant chunk scores higher"]),
    ("chapter 12", 6, ["with their similarity scores"]),
    ("chapter 12", 7, ["completely different scales", "0.87"]),
    ("chapter 13", 2, ["rough proxy for relevance", "The fourth chunk"]),
    ("chapter 13", 10, ["K = 10-30", "N = 3-5"]),
    ("chapter 15", 1, ["redundancy problem", "near-identical duplicates"]),
    ("Appendix", 20, ["Redundancy Problem"]),
    ("Appendix", 22, ["Top-K Retrieval", "vulnerable to redundancy"]),
    ("chapter 20", 1, ["cosine similarity scores look reasonable"]),
    ("chapter 20", 4, ["Vector similarity tells you how close"]),
    ("chapter 22", 4, ["Precision at K", "how much noise the retriever introduces"]),
    ("chapter 22", 11, ["Distracting noise is semantically similar to the query", "fifty percent noise"]),
]
for f, p, phrases in BOOKCHECKS:
    d = pymupdf.open(os.path.join(BOOK, f + ".pdf"))
    txt = norm(d[p - 1].get_text())
    for ph in phrases:
        check(f"{f} p.{p}/{len(d)} contains {ph!r}", ph in txt)

# absence scan: does the book give a rule for choosing K, or mention query/document input types?
absent = {"choose k / choosing k": r"\bchoos\w* (the )?k\b", "input_type / input type": r"input[_ ]type",
          "query prefix / instruction": r"query (prefix|instruction)", "argpartition": r"argpartition",
          "tie / tie-break": r"\bties?\b|tie-break"}
alltxt = {}
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    for i, pg in enumerate(pymupdf.open(f), 1):
        alltxt[f"{os.path.basename(f)} p.{i}"] = norm(pg.get_text())
for name, pat in absent.items():
    where = [k for k, v in alltxt.items() if re.search(pat, v, re.I)]
    print(f"INFO book scan {name}: {len(where)} pages {where[:8]}")

print(f"\n{'ALL PASS' if N_BAD == 0 else 'SOME FAILED'}: {N_OK} passed, {N_BAD} failed")
