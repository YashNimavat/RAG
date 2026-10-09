"""C3: check every repo-cell, helper-line, library-source and book-page citation in concepts/C3_embedding_indexing.md.

Read-only on all sources. Notebook cells are 0-based. helper_functions.py lines are 1-based. Book pages are 1-based
PDF pages of the split chapter files. Book phrases checked here are short (< 15 words); nothing is reproduced
in the lesson beyond them.
The third argument is OPTIONAL: a site-packages folder OUTSIDE the project env that holds langchain_community and
langchain_cohere (the learner's older venv). The files are only read as text; nothing is imported or installed.

Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C3/c3_sources.py "$B/upstream/RAG_Techniques" \
        "$B/RAG_Made_Simple_The_Complete_Visual_Guide" "C:/Yash/New-Work/RAG/RAG_Techniques-main/venv/Lib/site-packages" \
        > sources/verification/C3/out_c3_sources.txt
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

import pymupdf

REPO, BOOK = sys.argv[1], sys.argv[2]
SITE = sys.argv[3] if len(sys.argv) > 3 else None
fails = 0


def check(ok, label):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check(head == "009adba2be1bef49780ef73b6dd3c18fd24b035b", f"repo HEAD {head}")

# ---------------------------------------------------------------- helper_functions.py (1-based lines)
print("\n== helper_functions.py")
hf = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
for ln, needle in ((18, "def replace_t_with_space(list_of_documents):"),
                   (30, "doc.page_content = doc.page_content.replace('\\t', ' ')"),
                   (48, "def encode_pdf(path, chunk_size=1000, chunk_overlap=200):"),
                   (62, "loader = PyPDFLoader(path)"),
                   (67, "chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len"),
                   (69, "texts = text_splitter.split_documents(documents)"),
                   (70, "cleaned_texts = replace_t_with_space(texts)"),
                   (73, "embeddings = OpenAIEmbeddings()"),
                   (74, "vectorstore = FAISS.from_documents(cleaned_texts, embeddings)"),
                   (223, "def read_pdf_to_string(path):"),
                   (244, "content += page.get_text()"),
                   (338, "def get_langchain_embedding_provider(provider: EmbeddingProvider, model_id: str = None):"),
                   (354, "return OpenAIEmbeddings()"),
                   (357, "return CohereEmbeddings()")):
    check(needle in hf[ln - 1], f"helper_functions.py L{ln}: {needle}")

# ---------------------------------------------------------------- notebook cells (0-based)
print("\n== notebook cells (0-based)")
NB = "all_rag_techniques/"
CELLS = [
    ("simple_rag.ipynb", 10, ["def encode_pdf(path, chunk_size=1000, chunk_overlap=200):", "cleaned_texts = replace_t_with_space(texts)",
                              "get_langchain_embedding_provider(EmbeddingProvider.OPENAI)",
                              "vectorstore = FAISS.from_documents(cleaned_texts, embeddings)"]),
    ("local_rag_huggingface_faiss.ipynb", 10, ['EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"', "CHUNK_SIZE = 1000", "CHUNK_OVERLAP = 200"]),
    ("local_rag_huggingface_faiss.ipynb", 12, ["loader = PyPDFLoader(path)", "chunks = text_splitter.split_documents(documents)"]),
    ("local_rag_huggingface_faiss.ipynb", 14, ['encode_kwargs={"normalize_embeddings": True}']),
    ("local_rag_huggingface_faiss.ipynb", 16, ["def encode_to_faiss(chunks, embeddings):", "FAISS.from_documents(",
                                              '# vectorstore.save_local("faiss_climate_index")',
                                              '# vectorstore = FAISS.load_local("faiss_climate_index", embeddings, allow_dangerous_deserialization=True)']),
    ("hierarchical_indices.ipynb", 11, ['"chunk_id": i,', '"page": int(chunk.metadata.get("page", 0))',
                                        'metadata={"source": path, "page": doc.metadata["page"], "summary": True}',
                                        "embeddings = OpenAIEmbeddings()"]),
    ("hierarchical_indices.ipynb", 13, ['if os.path.exists("../vector_stores/summary_store") and os.path.exists("../vector_stores/detailed_store"):',
                                        'FAISS.load_local("../vector_stores/detailed_store", embeddings, allow_dangerous_deserialization=True)',
                                        'detailed_store.save_local("../vector_stores/detailed_store")']),
    ("context_enrichment_window_around_chunk.ipynb", 11, ["content = read_pdf_to_string(path)"]),
    ("context_enrichment_window_around_chunk.ipynb", 13, ['metadata={"index": len(chunks), "text": text}',
                                                          "start += chunk_size - chunk_overlap"]),
    ("context_enrichment_window_around_chunk.ipynb", 15, ["chunks_size = 400", "chunk_overlap = 200"]),
    ("context_enrichment_window_around_chunk.ipynb", 17, ["embeddings = OpenAIEmbeddings()", "FAISS.from_documents(docs, embeddings)"]),
    ("context_enrichment_window_around_chunk.ipynb", 23, ["chunk_size: int = 200, chunk_overlap: int = 20",
                                                          "current_index = chunk.metadata.get('index')"]),
    ("context_enrichment_window_around_chunk.ipynb", 25, ["chunk_size=400", "chunk_overlap=200"]),
    ("memorag.ipynb", 22, ["self.store.save_local(path)",
                           "FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)"]),
    ("reliable_rag.ipynb", 6, ['CohereEmbeddings(model="embed-english-v3.0")']),
]
for nb, i, needles in CELLS:
    cell = json.load(open(os.path.join(REPO, NB + nb), encoding="utf-8"))["cells"][i]
    src = "".join(cell["source"])
    for n in needles:
        check(cell["cell_type"] == "code" and n in src, f"{nb} cell {i}: {n}")

rs = open(os.path.join(REPO, "all_rag_techniques_runnable_scripts", "hierarchical_indices.py"), encoding="utf-8").read().splitlines()
check('os.path.exists("../vector_stores/summary_store")' in rs[93] and "save_local" in rs[99] and "save_local" in rs[100],
      "all_rag_techniques_runnable_scripts/hierarchical_indices.py L94 exists-check, L100-L101 save_local")

# ---------------------------------------------------------------- repo-wide scans (code only, comments stripped)
print("\n== repo-wide scans (all .ipynb code cells and .py files)")
hits = {k: [] for k in ("save_local", "load_local", "input_type", "manifest", "params_hash", "add_start_index",
                        "revision", "np.save(", "OpenAIEmbeddings()")}


def scan(rel, i, src):
    code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())   # drop comments
    for k in hits:
        if k in code:
            hits[k].append(f"{rel}" + (f" cell {i}" if i is not None else ""))


for f in sorted(glob.glob(os.path.join(REPO, "**", "*.ipynb"), recursive=True)):
    rel = os.path.relpath(f, REPO).replace("\\", "/")
    for i, c in enumerate(json.load(open(f, encoding="utf-8"))["cells"]):
        if c["cell_type"] == "code":
            scan(rel, i, "".join(c["source"]))
for f in sorted(glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True)):
    scan(os.path.relpath(f, REPO).replace("\\", "/"), None, open(f, encoding="utf-8", errors="replace").read())
for k, v in hits.items():
    print(f"INFO {k!r}: {len(v)} -> {v[:12]}{' …' if len(v) > 12 else ''}")
check(not hits["input_type"], "no code anywhere in the repo sets an embedding input_type")
check(not hits["manifest"] and not hits["params_hash"], "no index manifest or params hash anywhere in the repo")
check(not hits["revision"], "no model revision pinned anywhere in the repo")

# ---------------------------------------------------------------- library source (read as text, not run)
print("\n== library source (learner's older venv; read as text, not imported)")
if SITE and os.path.isdir(SITE):
    for rel, checks in [
        ("langchain_community/vectorstores/faiss.py",
         [(1147, "def save_local(self, folder_path: str, index_name: str = \"index\") -> None:"),
          (1160, 'faiss.write_index(self.index, str(path / f"{index_name}.faiss"))'),
          (1164, "pickle.dump((self.docstore, self.index_to_docstore_id), f)"),
          (1167, "def load_local("), (1170, "embeddings: Embeddings,"),
          (1173, "allow_dangerous_deserialization: bool = False,"),
          (1216, "return cls(embeddings, index, docstore, index_to_docstore_id, **kwargs)")]),
        ("langchain_cohere/embeddings.py",
         [(47, "model: Optional[str] = None"), (109, "if not self.model:"),
          (195, 'return self.embed(texts, input_type="search_document")'),
          (217, 'return self.embed([text], input_type="search_query")[0]')]),
    ]:
        p = os.path.join(SITE, rel)
        lines = open(p, encoding="utf-8").read().splitlines()
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        print(f"INFO {rel} sha256 {sha}")
        for ln, needle in checks:
            check(needle in lines[ln - 1], f"{rel} L{ln}: {needle}")
    for dist in ("langchain_community", "langchain_cohere"):
        found = glob.glob(os.path.join(SITE, dist + "-*.dist-info"))
        print("INFO", dist, "version:", os.path.basename(found[0]) if found else "not found")
    sv = open(os.path.join(SITE, "langchain_community/vectorstores/faiss.py"), encoding="utf-8").read()
    body = sv[sv.index("def save_local("):sv.index("def load_local(")]
    check("embedding" not in body.replace("embeddings", "").lower() and "model" not in body.lower(),
          "save_local writes no embedding-model identity (only index.faiss + index.pkl)")
else:
    print("SKIP library checks (no site-packages argument): LangChain/Cohere claims stay UNVERIFIED")

# ---------------------------------------------------------------- book pages (1-based PDF pages)
print("\n== book pages")


def page_text(chapter, p):
    doc = pymupdf.open(os.path.join(BOOK, f"{chapter}.pdf"))
    return " ".join(doc[p - 1].get_text().split()), len(doc)


PAGES = [
    ("chapter 1", 5, ["Step 3: Clean the Text", "Dirty text leads to noisy embeddings", "Step 4: Create Embeddings"]),
    ("chapter 1", 6, ["Step 5: Store in a Vector Database", "even with millions of entries"]),
    ("chapter 1", 7, ["Algorithm Sketch: Document Preparation", "Clean each chunk (remove formatting artifacts)",
                      "Store all vectors in a vector store"]),
    ("chapter 1", 12, ["You never update your document collection"]),
    ("chapter 7", 4, ["The technique modifies only the preparation phase"]),
    ("chapter 8", 4, ["Store Position Metadata During Chunking", "sequential index", "given an index number"]),
    ("chapter 11", 6, ["pointer back to the parent chunk"]),
    ("chapter 11", 10, ["every time the collection updates", "front-loads the investment"]),
    ("chapter 13", 6, ["document embeddings can be precomputed and stored"]),
    ("chapter 14", 9, ["The Role of Metadata", "The simplest metadata scheme uses page numbers"]),
    ("chapter 14", 10, ["document identifiers combined with section numbers"]),
    ("chapter 15", 12, ["requires no changes to the index, embedding model, or preparation pipeline"]),
    ("chapter 16", 4, ["tagged with metadata noting which page it came from"]),
    ("Appendix", 16, ["Embedding A list of numbers"]),
    ("Appendix", 22, ["Vector Database / Vector Store"]),
]
for ch, p, needles in PAGES:
    t, n = page_text(ch, p)
    for nd in needles:
        assert len(nd.split()) < 15
        check(nd in t, f"{ch} p.{p}/{n}: '{nd}'")

print("\n== book-wide absence scan (whole book, case-insensitive)")
TERMS = {"hash": r"\bhash", "manifest (as a file)": r"\bmanifest\.|manifest file", "cache": r"\bcach",
         "re-index / reindex": r"\bre-?index", "rebuild": r"\brebuil", "re-embed": r"\bre-?embed",
         "input type": r"input[ _]type", "search_query": r"search_query", "normalize vectors": r"normali[sz]e[ds]? (the )?(embedding|vector)",
         "unit length": r"unit[- ]length", "model revision": r"revision", "pickle": r"pickle"}
found = {k: [] for k in TERMS}
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    doc = pymupdf.open(f)
    for i, pg in enumerate(doc):
        t = " ".join(pg.get_text().split())
        for k, rx in TERMS.items():
            if re.search(rx, t, re.I):
                found[k].append(f"{os.path.basename(f)[:-4]} p.{i + 1}/{len(doc)}")
for k, v in found.items():
    print(f"INFO book '{k}': {len(v)} page(s) {v}")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
sys.exit(1 if fails else 0)
