"""C6: check every repo-cell, script-line and book-page citation in concepts/C6_v0_pipeline.md against the files.

Read-only on both sources. Cells are 0-based. Book pages are 1-based PDF pages of the split chapter files.
Book phrases checked here are short (each under 15 words); the lesson paraphrases them.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C6/c6_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide" [<reference run dir>]
Saved output: sources/verification/C6/out_c6_sources.txt
"""
import json
import os
import subprocess
import sys

import pymupdf

REPO, BOOK = sys.argv[1], sys.argv[2]
RUN = sys.argv[3] if len(sys.argv) > 3 else None
fails = 0


def check(ok, label):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check(head == "009adba2be1bef49780ef73b6dd3c18fd24b035b", f"repo HEAD {head}")
T = "all_rag_techniques/"


def nb(name):
    return json.load(open(os.path.join(REPO, T + name), encoding="utf-8"))["cells"]


def src(cells, i):
    return "".join(cells[i]["source"])


# ---------------------------------------------------------------- simple_rag.ipynb, end to end
print("\n== simple_rag.ipynb (22 cells, 0-based)")
s = nb("simple_rag.ipynb")
check(len(s) == 22, f"simple_rag.ipynb has {len(s)} cells")
check(sum(c["cell_type"] == "code" for c in s) == 11, "11 code cells")
check("!pip install PyMuPDF==1.26.1" in src(s, 3) and "!pip install pypdf==5.6.0" in src(s, 3), "cell 3 installs pypdf 5.6.0 AND PyMuPDF 1.26.1")
check("from google.colab import userdata" in src(s, 5) and "OPENAI_API_KEY" in src(s, 5), "cell 5 needs Colab userdata + OPENAI_API_KEY")
check("from evaluation.evalute_rag import evaluate_rag" in src(s, 5), "cell 5 imports evaluate_rag")
c10 = src(s, 10)
for needle in ["def encode_pdf(path, chunk_size=1000, chunk_overlap=200):", "loader = PyPDFLoader(path)",
               "chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len",
               "texts = text_splitter.split_documents(documents)", "cleaned_texts = replace_t_with_space(texts)",
               "get_langchain_embedding_provider(EmbeddingProvider.OPENAI)", "FAISS.from_documents(cleaned_texts, embeddings)"]:
    check(needle in c10, f"cell 10: {needle}")
check(c10.index("split_documents") < c10.index("replace_t_with_space(texts)"), "cell 10 cleans AFTER splitting (same order as the book's sketch)")
check("add_start_index" not in c10 and "fitz" not in c10 and "pymupdf" not in c10.lower(), "cell 10: no start index (no offsets); PyMuPDF installed but not used")
check('encode_pdf(path, chunk_size=1000, chunk_overlap=200)' in src(s, 11), "cell 11 builds the store at 1000/200")
check('search_kwargs={"k": 2}' in src(s, 13), "cell 13 k=2")
check("retrieve_context_per_question(test_query, chunks_query_retriever)" in src(s, 15) and "show_context(context)" in src(s, 15), "cell 15 retrieves and prints")
out15 = "".join("".join(o.get("text", "")) for o in s[15]["outputs"] if o.get("name") == "stdout")
check(out15.count("Context ") == 2 and "score" not in out15.lower() and "page" not in out15.lower(), "cell 15 saved output: 2 contexts, no score, no page")
check("evaluate_rag(chunks_query_retriever)" in src(s, 17), "cell 17 runs evaluate_rag (OpenAI only)")
check(not any(k in src(s, i) for i in range(len(s)) if s[i]["cell_type"] == "code"
              for k in ("ChatOpenAI", "invoke(", "llm(", "generate(")), "no code cell generates an answer (no LLM call outside evaluate_rag)")

# ---------------------------------------------------------------- helper_functions.py
print("\n== helper_functions.py lines")
L = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
check(L[17].startswith("def replace_t_with_space") and "replace('\\t', ' ')" in L[29], "L18 replace_t_with_space; L30 replaces tabs only")
check(L[47].startswith("def encode_pdf(path, chunk_size=1000, chunk_overlap=200):"), "L48 encode_pdf")
check("PyPDFLoader(path)" in L[61] and "split_documents" in L[68] and "replace_t_with_space(texts)" in L[69], "L62 PyPDFLoader, L69 split, L70 clean after split")
check("OpenAIEmbeddings()" in L[72] and "FAISS.from_documents" in L[73], "L73 OpenAIEmbeddings, L74 FAISS")
check(L[128].startswith("def retrieve_context_per_question"), "L129 retrieve_context_per_question")
check("get_relevant_documents(question)" in L[142], "L143 get_relevant_documents")
check(L[146].strip() == "context = [doc.page_content for doc in docs]", "L147 keeps page_content only: metadata and scores dropped")
check(L[207].startswith("def show_context"), "L208 show_context")
check("EmbeddingProvider.COHERE" in "\n".join(L[335:362]) and "CohereEmbeddings()" in "\n".join(L[335:362]),
      "L336-L362 get_langchain_embedding_provider also offers Cohere (unused by simple_rag)")

# ---------------------------------------------------------------- runnable script
print("\n== all_rag_techniques_runnable_scripts/simple_rag.py")
R = open(os.path.join(REPO, "all_rag_techniques_runnable_scripts/simple_rag.py"), encoding="utf-8").read().splitlines()
check(R[17].startswith("class SimpleRAG:"), "L18 class SimpleRAG")
check("n_retrieved=2" in R[22], "L23 n_retrieved=2 default")
check("start_time = time.time()" in R[35] and "'Chunking'" in R[37], "L36-L38 times the whole encode_pdf call and labels it 'Chunking'")
check("start_time = time.time()" in R[54] and "'Retrieval'" in R[56], "L55-L57 retrieval timing")
check("show_context(context)" in R[60], "L61 prints the context; nothing is returned or logged")

# ---------------------------------------------------------------- local_rag_huggingface_faiss.ipynb
print("\n== local_rag_huggingface_faiss.ipynb")
h = nb("local_rag_huggingface_faiss.ipynb")
check(all(len(c.get("outputs", [])) == 0 for c in h), "no cell has a saved output (not executed at this commit)")
check("TOP_K = 3" in src(h, 10) and 'EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"' in src(h, 10) and "zephyr-7b-beta" in src(h, 10), "cell 10: TOP_K=3, bge-base, zephyr")
check("PyPDFLoader(path)" in src(h, 12), "cell 12 PyPDFLoader")
check('"normalize_embeddings": True' in src(h, 14), "cell 14 normalized embeddings")
check("FAISS.from_documents(" in src(h, 16), "cell 16 FAISS")
check("doc.metadata.get(\"page\", \"?\")" in src(h, 18), "cell 18 prints page metadata (no scores)")
check("HuggingFaceEndpoint(" in src(h, 20), "cell 20 remote HuggingFaceEndpoint")
check("using ONLY the context provided below" in src(h, 22), "cell 22 context-only prompt")
check("[Page {doc.metadata.get('page', '?')}]" in src(h, 24), "cell 24 [Page n] labels")
check('split("Answer:")[-1]' in src(h, 26), "cell 26 ask() keeps the text after the last 'Answer:'")
check("RunnableParallel(" in src(h, 28) and "sources=retriever" in src(h, 28), "cell 28 returns answer + sources")
check("evaluate_rag(rag_chain, retriever)" in src(h, 30), "cell 30 calls evaluate_rag(rag_chain, retriever)")
E = open(os.path.join(REPO, "evaluation/evalute_rag.py"), encoding="utf-8").read()
check("def evaluate_rag(retriever, num_questions: int = 5)" in E and "retriever.get_relevant_documents(question)" in E,
      "evalute_rag.py: signature (retriever, num_questions); calls retriever.get_relevant_documents (so cell 30 passes a chain as 'retriever', by reading; not run)")

# ---------------------------------------------------------------- simple_rag_with_llamaindex.ipynb
print("\n== simple_rag_with_llamaindex.ipynb")
li = nb("simple_rag_with_llamaindex.ipynb")
check("CHUNK_SIZE = 200" in src(li, 4) and "CHUNK_OVERLAP = 50" in src(li, 4) and "Settings.embed_model" in src(li, 4), "cell 4: 200/50 tokens, global Settings.embed_model")
check("node.text.replace('\\t', ' ')" in src(li, 11) and "replace(' \\n', ' ')" in src(li, 11), "cell 11 TextCleaner (tabs and ' \\n')")
check("SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)" in src(li, 13)
      and src(li, 13).index("TextCleaner()") < src(li, 13).index("text_splitter,"), "cell 13: cleaner runs BEFORE the splitter")
check("VectorStoreIndex(nodes)" in src(li, 16) and "similarity_top_k=2" in src(li, 16), "cell 16: VectorStoreIndex(nodes), k=2")
check("as_query_engine(similarity_top_k=2)" in src(li, 23), "cell 23 query engine")

# ---------------------------------------------------------------- repo test query vs our reference ranks
if RUN:
    print("\n== repo cell 15 saved contexts vs the C6 reference run (R-001)")
    import glob
    cj = glob.glob(os.path.join(RUN, "index", "*", "*", "*", "chunks.jsonl"))[0]
    rows = [json.loads(l) for l in open(cj, encoding="utf-8")]
    rec = [json.loads(l) for l in open(os.path.join(RUN, "results.jsonl"), encoding="utf-8")]
    r001 = next(r for r in rec if r["qid"] == "R-001")
    byid = {r["chunk_id"]: r for r in rows}
    ctx = out15.split("Context 2:")
    norm = lambda t: " ".join(t.split())
    for rank, saved in ((1, ctx[0].replace("Context 1:", "")), (2, ctx[1])):
        ours = byid[r001["candidates"]["dense"][rank - 1]["chunk_id"]]["text"]
        check(norm(ours)[:120] == norm(saved)[:120], f"our rank {rank} for R-001 starts like the repo's saved Context {rank} (first 120 chars, whitespace-normalised)")

# ---------------------------------------------------------------- book
print("\n== book pages")


def page(fname, p):
    return " ".join(pymupdf.open(os.path.join(BOOK, fname))[p - 1].get_text().split())


def count(fname):
    return len(pymupdf.open(os.path.join(BOOK, fname)))


check(count("chapter 1.pdf") == 14 and count("Appendix.pdf") == 23 and count("chapter 22.pdf") == 19 and count("intro.pdf") == 8, "page totals Ch1 14, App 23, Ch22 19, Intro 8")
BOOKCHECKS = [
    ("chapter 1.pdf", 1, ["The Problem", "hallucination", "answering from memory"]),
    ("chapter 1.pdf", 2, ["The Core Idea", "closed-book exam"]),
    ("chapter 1.pdf", 3, ["How It Works", "two phases", "offline preparation phase"]),
    ("chapter 1.pdf", 4, ["Step 1: Load the Document", "page by page", "Poor text extraction", "Step 2: Split Into Chunks", "about 1,000 characters", "200 characters of overlap"]),
    ("chapter 1.pdf", 5, ["Step 3: Clean the Text", "stray tab", "Step 4: Create Embeddings"]),
    ("chapter 1.pdf", 6, ["Step 5: Store in a Vector Database", "FAISS"]),
    ("chapter 1.pdf", 7, ["Algorithm Sketch: Document Preparation", "Clean each chunk", "Split text into chunks"]),
    ("chapter 1.pdf", 8, ["Phase 2: Answering a Query", "Step 6: Embed the Query", "exact same process", "Step 7: Find the Nearest Chunks", "top 2 to 5"]),
    ("chapter 1.pdf", 9, ["Step 8: Generate the Answer", "grounded in the actual document content"]),
    ("chapter 1.pdf", 10, ["Algorithm Sketch: Query Processing", "top-K nearest chunk vectors", "The Role of Chunk Size", "100 characters"]),
    ("chapter 1.pdf", 11, ["5,000 characters", "Just right", "Where Simple RAG Falls Short"]),
    ("chapter 1.pdf", 12, ["scattered across multiple sections", "not bugs", "When to Use This", "Overkill when"]),
    ("chapter 1.pdf", 13, ["one embedding call", "depends entirely on retrieval quality", "Key Takeaways"]),
    ("chapter 1.pdf", 14, ["foundation that all advanced techniques"]),
    ("Appendix.pdf", 4, ["retrieves the wrong documents"]),
    ("Appendix.pdf", 5, ["The final answer is wrong or made up", "cannot measure or improve it"]),
    ("Appendix.pdf", 6, ["Layer 1: Foundation", "end to end", "Do not optimize prematurely"]),
    ("Appendix.pdf", 7, ["most common mistake"]),
    ("chapter 22.pdf", 8, ["isolates generation quality from retrieval quality"]),
    ("chapter 22.pdf", 13, ["Component-Level Versus End-to-End Evaluation", "tell you where to look"]),
    ("chapter 22.pdf", 14, ["per-component breakdown"]),
    ("intro.pdf", 7, ["read Chapter 1 first"]),
]
for f, p, needles in BOOKCHECKS:
    t = page(f, p)
    for n in needles:
        check(n in t, f"{f} p.{p}: {n!r}")
ch1 = " ".join(page("chapter 1.pdf", p) for p in range(1, 15)).lower()
for absent in ("trace", "citation", "cite ", "provenance", "metadata", "page number", "score", "offset", "reproduc"):
    check(absent not in ch1, f"Ch1 (all 14 pages) never mentions {absent.strip()!r}")
check(ch1.index("step 2: split into chunks") < ch1.index("step 3: clean the text"), "Ch1: split (Step 2) comes before clean (Step 3)")
print("\nALL PASS" if not fails else f"\n{fails} FAIL")
sys.exit(1 if fails else 0)
