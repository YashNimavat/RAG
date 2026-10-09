"""P7: check every repo-cell and book-page citation in concepts/P7_grounded_prompting.md against the files.

Read-only on both sources. Cells are 0-based. Book pages are 1-based PDF pages of the split chapter files.
Book phrases checked here are short (each under 15 words); the lesson paraphrases them.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P7/p7_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/P7/out_p7_sources.txt
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


def cell(nb, i):
    c = json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]
    return c["cell_type"], "".join(c["source"]), c.get("outputs", [])


T = "all_rag_techniques/"
CELLS = [
    (T + "simple_csv_rag.ipynb", 16, ["Use the following pieces of retrieved context", "If you don't know the answer, say that you ",
                                      "\"{context}\"", "create_stuff_documents_chain(llm, prompt)", "vector_store.as_retriever()"]),
    (T + "local_rag_huggingface_faiss.ipynb", 18, ['search_kwargs={"k": TOP_K}']),
    (T + "local_rag_huggingface_faiss.ipynb", 20, ["max_new_tokens=256", "temperature=0.1"]),
    (T + "local_rag_huggingface_faiss.ipynb", 22, ["using ONLY the context provided below",
                                                   "If the answer is not contained in the context, respond with:",
                                                   "Do not use any prior knowledge or make assumptions."]),
    (T + "local_rag_huggingface_faiss.ipynb", 24, ["[Page {doc.metadata.get('page', '?')}]", "def format_docs(docs):"]),
    (T + "local_rag_huggingface_faiss.ipynb", 26, ["What is the GDP of India in 2024?", "Out-of-scope"]),
    (T + "local_rag_huggingface_faiss.ipynb", 12, ["PyPDFLoader(path)"]),
    (T + "reliable_rag.ipynb", 18, ["Answer the question based upon your knowledge.", "<docs>{documents}</docs>",
                                    'ChatGroq(model="llama-3.1-8b-instant", temperature=0)', "Source:{doc.metadata['source']}"]),
    (T + "reliable_rag.ipynb", 20, ["You are a grader assessing whether an LLM generation is grounded"]),
    (T + "multi_model_rag_with_captioning.ipynb", 12, ["You are an assistant tasked with summarizing tables, images and text for retrieval."]),
    (T + "multi_model_rag_with_captioning.ipynb", 14, ['metadata={"name": text[\'name\']}', "chunk_size=400, chunk_overlap=50"]),
    (T + "multi_model_rag_with_captioning.ipynb", 15, ["search_kwargs={'k': 1}"]),
    (T + "multi_model_rag_with_captioning.ipynb", 17, ['query = "What is the BLEU score of the Transformer (base model)?"']),
    (T + "multi_model_rag_with_captioning.ipynb", 20, ["Answer the question based upon your knowledge.",
                                                       'ChatCohere(model="command-r-plus", temperature=0)',
                                                       '"documents":docs[0].page_content']),
]
for nb, i, needles in CELLS:
    kind, src, _ = cell(nb, i)
    check(kind == "code", f"{nb} cell {i} is a code cell")
    for n in needles:
        check(n in src, f"{nb} cell {i}: {n}")
# saved outputs that the lesson mentions
_, _, out = cell(T + "multi_model_rag_with_captioning.ipynb", 20)
txt = "".join("".join(o.get("text", "")) for o in out)
check("BLEU score of 27.3" in txt, "captioning cell 20 saved output states a BLEU number (27.3)")
for i in (17, 18):
    check(len(cell(T + "multi_model_rag_with_captioning.ipynb", i)[2]) == 0, f"captioning cell {i}: no saved output (retrieved chunk not saved)")
check(len(json.load(open(os.path.join(REPO, T + "multi_model_rag_with_captioning.ipynb"), encoding="utf-8"))["cells"]) == 22,
      "captioning notebook has 22 cells (0-21)")

# helper_functions.py L162-L205: the context-only QA chain, and who calls it
lines = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
check(lines[161].startswith("def create_question_answer_from_context_chain(llm):"), "helper_functions.py L162 def create_question_answer_from_context_chain")
check('return {"answer": answer, "context": context, "question": question}' in lines[204], "helper_functions.py L205 ends answer_question_from_context")
check(any("based ONLY on the provided context" in l for l in lines[161:205]), "helper L162-L205: 'based ONLY on the provided context'")
users = []
for f in glob.glob(os.path.join(REPO, "**", "*.ipynb"), recursive=True) + glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True):
    if "create_question_answer_from_context_chain(" in open(f, encoding="utf-8", errors="ignore").read() or \
       "answer_question_from_context(" in open(f, encoding="utf-8", errors="ignore").read():
        users.append(os.path.relpath(f, REPO).replace("\\", "/"))
check(sorted(users) == ["helper_functions.py"], f"only helper_functions.py calls/defines them with '(' : {sorted(users)}")
ev = open(os.path.join(REPO, "evaluation/evalute_rag.py"), encoding="utf-8").read()
check("create_question_answer_from_context_chain," in ev and "create_question_answer_from_context_chain(" not in ev,
      "evaluation/evalute_rag.py imports the chain but never calls it")


# ---------------------------------------------------------------- book
def page(f, p):
    d = fitz.open(os.path.join(BOOK, f))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


BOOKP = [  # (file, page, total, short phrase that must be on that page)
    ("chapter 1.pdf", 1, 14, "It is answering from memory"),
    ("chapter 1.pdf", 3, 14, "stuff entire documents into the prompt"),
    ("chapter 1.pdf", 9, 14, "Step 8: Generate the Answer"),
    ("chapter 1.pdf", 9, 14, "not in its training memory"),
    ("chapter 1.pdf", 10, 14, "Pass question + retrieved chunks to the language model"),
    ("chapter 3.pdf", 5, 14, "Step 3: Generate an Answer"),
    ("chapter 3.pdf", 5, 14, "removes noise that would otherwise distract"),
    ("chapter 3.pdf", 6, 14, "identical to the generation step in simple RAG"),
    ("chapter 3.pdf", 6, 14, "Even with perfect context"),
    ("chapter 3.pdf", 8, 14, "adding footnotes to a research paper"),
    ("chapter 3.pdf", 11, 14, "is better than a confident wrong answer"),
    ("chapter 16.pdf", 6, 11, "The captioning prompt should instruct the model"),
    ("chapter 16.pdf", 6, 11, "It runs once during preparation, not at query time"),
    ("chapter 16.pdf", 8, 11, "At query time, nothing changes."),
    ("chapter 16.pdf", 8, 11, "What is the BLEU score of the base model?"),
    ("chapter 22.pdf", 5, 19, "give more weight to documents that appear first"),
    ("chapter 22.pdf", 8, 19, "the problem is in the language model or the prompt"),
    ("chapter 22.pdf", 16, 19, "Prompt injection attacks attempt to override"),
    ("Appendix.pdf", 15, 23, "give more weight to documents appearing first"),
    ("Appendix.pdf", 17, 23, "A grounded answer can be traced back"),
]
for f, p, tot, phrase in BOOKP:
    t, n = page(f, p)
    check(n == tot, f"{f} has {tot} pages")
    check(len(phrase.split()) < 15, f"phrase under 15 words: {phrase!r}")
    check(phrase in t, f"{f} p.{p}/{tot}: {phrase!r}")

# absence checks over the whole book
allp = []
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    d = fitz.open(f)
    allp += [(os.path.basename(f), i + 1, re.sub(r"\s+", " ", pg.get_text())) for i, pg in enumerate(d)]
check(not any(re.search(r"lost in the middle", t, re.I) for _, _, t in allp), "book: no 'lost in the middle' anywhere")
check(not any(re.search(r"\bLiu\b", t) for _, _, t in allp), "book: no 'Liu' anywhere")
first = [(f, p) for f, p, t in allp if re.search(r"appear(s|ing)? first", t, re.I)]
print("pages with 'appear(s/ing) first':", first)
check(first == [("Appendix.pdf", 15), ("chapter 22.pdf", 5)], "the first-position claim appears only at Ch22 p.5/19 and Appendix p.15/23")
cite_pages = [(f, p) for f, p, t in allp if re.search(r"\bcit(e|es|ation|ations)\b", t, re.I)]
print("pages mentioning cite/citation:", cite_pages)

print("ALL PASS" if fails == 0 else f"{fails} FAIL(S)")
sys.exit(1 if fails else 0)
