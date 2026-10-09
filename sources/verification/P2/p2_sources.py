"""P2: check every repo-cell and book-page citation in concepts/P2_ir_framing.md against the files.

Read-only on both sources. Cells are 0-based. Book pages are 1-based PDF pages of the split chapter files.
Every book phrase checked here is shorter than 15 words.
Run from rag_learning/:
    uv run python sources/verification/P2/p2_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/P2/out_p2_sources.txt
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
    return "".join(json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]["source"])


# (notebook, 0-based cell, literal substrings that must all be in that cell)
CELLS = [
    ("all_rag_techniques/simple_rag.ipynb", 13, ['as_retriever(search_kwargs={"k": 2})']),
    ("all_rag_techniques/fusion_retrieval.ipynb", 14,
     ["def create_bm25_index(", "BM25 (Best Matching 25) is a ranking function used in information retrieval",
      "doc.page_content.split()", "return BM25Okapi(tokenized_docs)"]),
    ("all_rag_techniques/fusion_retrieval.ipynb", 17,
     ['vectorstore.similarity_search("", k=vectorstore.index.ntotal)', "bm25.get_scores(query.split())",
      "np.argsort(combined_scores)[::-1]", "sorted_indices[:k]"]),
    ("all_rag_techniques/reliable_rag.ipynb", 14,
     ["Binary score for relevance check on retrieved documents.",
      "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.",
      "It does not need to be a stringent test.", 'ChatGroq(model="llama-3.1-8b-instant", temperature=0)']),
    ("evaluation/define_evaluation_metrics.ipynb", 3, ["Ground Truth: {ground_truth}", "ground_truth: The ground truth answer."]),
    ("evaluation/define_evaluation_metrics.ipynb", 9,
     ["0.33 - Somewhat relevant: Contains related keywords or concepts",
      "1.00 - Highly relevant: Directly and fully answers the question",
      "Final Score: [Average of all scores]", "relevancy_score_prompt = PromptTemplate(",
      "ratio_of_relevant_docs_chain = ratio_of_relevant_docs_prompt |"]),
    ("evaluation/evaluation_deep_eval.ipynb", 6, ["ContextualRelevancyMetric(", "retrieval_context=retrieval_context"]),
    ("evaluation/evaluation_deep_eval.ipynb", 11,
     ["def create_deep_eval_test_cases(questions, gt_answers, generated_answers, retrieved_documents)",
      "expected_output=gt_answer", "retrieval_context=retrieved_document"]),
]
for nb, i, needles in CELLS:
    src = cell(nb, i)
    for n in needles:
        check(n in src, f"{nb} cell {i}: {n}")
# define_evaluation_metrics cell 9 names the prompt relevancy_score_prompt but uses ratio_of_relevant_docs_prompt (NameError)
src9 = cell("evaluation/define_evaluation_metrics.ipynb", 9)
check("ratio_of_relevant_docs_prompt =" not in src9, "define_evaluation_metrics.ipynb cell 9: ratio_of_relevant_docs_prompt is never defined there")

# data/q_a.json holds questions and answers only (no relevant-document labels)
qa = json.load(open(os.path.join(REPO, "data", "q_a.json"), encoding="utf-8"))
check(len(qa) == 44 and all(set(x) == {"question", "answer"} for x in qa), "data/q_a.json: 44 items, keys {question, answer} only")

# Absences across the repo: no inverted index and no qrels in any source cell, .py or .md file
hits = {"inverted": [], "qrel": []}
for f in glob.glob(os.path.join(REPO, "**", "*"), recursive=True):
    if f.endswith(".ipynb"):
        texts = ["".join(c["source"]) for c in json.load(open(f, encoding="utf-8"))["cells"]]
    elif f.endswith((".py", ".md")):
        texts = [open(f, encoding="utf-8", errors="replace").read()]
    else:
        continue
    for t in texts:
        for k in hits:
            if re.search(k, t, re.I):
                hits[k].append(os.path.relpath(f, REPO))
for k, v in hits.items():
    check(not v, f"repo: no '{k}' in any notebook source cell, .py or .md file (hits: {sorted(set(v))})")


def page(chapter_file, p):
    d = fitz.open(os.path.join(BOOK, chapter_file))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


# (file, 1-based page, expected page count, phrase that must appear; every phrase < 15 words)
PAGES = [
    ("intro.pdf", 1, 8, "retrieved passages are almost-but-not-quite"),
    ("chapter 1.pdf", 8, 14, "Find the Nearest Chunks"),
    ("chapter 1.pdf", 8, 14, "most likely to contain the answer"),
    ("chapter 1.pdf", 10, 14, "Search vector store for top-K nearest chunk vectors"),
    ("chapter 1.pdf", 12, 14, "will miss most of the relevant material"),
    ("chapter 1.pdf", 12, 14, "You only need keyword search"),
    ("chapter 3.pdf", 1, 14, "Similarity search returns the closest chunks by meaning"),
    ("chapter 3.pdf", 1, 14, "page footer stuffed with navigation links"),
    ("chapter 12.pdf", 2, 14, "The meaning is there. The words are not."),
    ("chapter 12.pdf", 3, 14, "The index tells you exactly which pages mention those words."),
    ("chapter 12.pdf", 5, 14, "It works purely with words"),
    ("chapter 12.pdf", 6, 14, "One index understands meaning. The other counts words."),
    ("chapter 13.pdf", 1, 13, "None of them names Paris."),
    ("chapter 13.pdf", 2, 13, "embedding similarity is a rough proxy for relevance"),
    ("chapter 13.pdf", 5, 13, "makes it into the candidate set"),
    ("chapter 13.pdf", 9, 13, "pairs labeled as relevant or not relevant"),
    ("chapter 22.pdf", 4, 19, "precision at five is 0.6"),
    ("chapter 22.pdf", 5, 19, "recall is 0.3"),
    ("chapter 22.pdf", 5, 19, "accounts for ranking order"),
    ("chapter 22.pdf", 6, 19, "what was retrieved but not how well it was ranked"),
    ("chapter 22.pdf", 7, 19, "even when both lists contain the same documents"),
    ("chapter 22.pdf", 12, 19, "paired with the expected relevant documents and a reference answer"),
    ("Appendix.pdf", 19, 23, "Precision at K"),
    ("Appendix.pdf", 20, 23, "Recall at K"),
    ("Appendix.pdf", 20, 23, "Relevancy Grading"),
    ("Appendix.pdf", 22, 23, "returning the K chunks with the highest similarity scores"),
]
for f, p, total, phrase in PAGES:
    t, n = page(f, p)
    check(n == total and phrase in t and len(phrase.split()) < 15, f"Ch {f} p.{p}/{n}: '{phrase}'")

# Book absences: 'inverted' and 'qrel' never appear; 'relevance judg' only once (App p.9/23, about reranking)
found = {"inverted": [], "qrel": [], "relevance judg": []}
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    d = fitz.open(f)
    for i, pg in enumerate(d):
        t = re.sub(r"\s+", " ", pg.get_text())
        for k in found:
            if re.search(k, t, re.I):
                found[k].append(f"{os.path.basename(f)} p.{i + 1}/{len(d)}")
check(not found["inverted"], f"book: 'inverted' never appears ({found['inverted']})")
check(not found["qrel"], f"book: 'qrel' never appears ({found['qrel']})")
check(found["relevance judg"] == ["Appendix.pdf p.9/23"], f"book: 'relevance judg' only at {found['relevance judg']}")

print("\nALL PASS" if fails == 0 else f"\n{fails} FAIL(S)")
