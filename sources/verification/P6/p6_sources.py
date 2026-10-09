"""P6: check every repo-cell and book-page citation in concepts/P6_ir_metrics.md, and re-run the
repo-wide search for rank metrics.

Read-only on both sources. Notebook cells are 0-based. Book pages are 1-based PDF pages of the split
chapter files. Book phrases checked here are short (< 15 words each).
Run from rag_learning/:
    uv run python sources/verification/P6/p6_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/P6/out_p6_sources.txt
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


# ------------------------------------------------------------------ 1. repo-wide search for rank metrics
print("\n=== R1 repo-wide search (cell sources + text outputs of every notebook; every line of every .py)")
PAT = re.compile(r"ndcg|\bdcg\b|discounted cumulative|reciprocal[ _]rank|\bmrr\b|recall@|recall_at|recall at k|"
                 r"hit[ _]?rate|hits?@|precision@|precision_at|precision at k|average_precision|"
                 r"mean average precision|\bmap@", re.I)
nbs = sorted(glob.glob(os.path.join(REPO, "**", "*.ipynb"), recursive=True))
pys = sorted(glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True))
hits, image_hits = [], set()
for f in nbs:
    rel = os.path.relpath(f, REPO).replace("\\", "/")
    for i, c in enumerate(json.load(open(f, encoding="utf-8"))["cells"]):
        src = "".join(c.get("source", []))
        txt = ""
        for o in c.get("outputs", []):
            txt += "".join(o.get("text", []))
            for mime, val in o.get("data", {}).items():
                v = "".join(val) if isinstance(val, list) else str(val)
                if mime.startswith("image/"):
                    if PAT.search(v):
                        image_hits.add(rel)
                else:
                    txt += v
        for m in PAT.finditer(src):
            hits.append(f"{rel} cell {i} source: {m.group(0)!r}")
        for m in PAT.finditer(txt):
            hits.append(f"{rel} cell {i} output: {m.group(0)!r}")
for f in pys:
    rel = os.path.relpath(f, REPO).replace("\\", "/")
    for n, line in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
        for m in PAT.finditer(line):
            hits.append(f"{rel}:L{n}: {m.group(0)!r}")
print(f"scanned {len(nbs)} notebooks and {len(pys)} .py files")
for h in hits:
    print("  hit:", h)
print("  matches only inside base64 image outputs (not text):", sorted(image_hits))
check(hits == ["all_rag_techniques/local_rag_huggingface_faiss.ipynb cell 30 source: 'hit rate'"],
      "the only rank-metric-like term in code or text is 'hit rate' in local_rag_huggingface_faiss.ipynb cell 30")

# ------------------------------------------------------------------ 2. cited cells and lines
print("\n=== R2 cited cells (0-based) and lines")
CELLS = [
    ("all_rag_techniques/local_rag_huggingface_faiss.ipynb", 30,
     ["evaluate_rag(rag_chain, retriever)", "except ImportError", "expected_keywords",
      "kw.lower() in answer", 'len(pair["expected_keywords"])', "Keyword hit rate"]),
    ("evaluation/define_evaluation_metrics.ipynb", 3, ["correctness_prompt = PromptTemplate("]),
    ("evaluation/define_evaluation_metrics.ipynb", 6, ["faithfulness_prompt = PromptTemplate("]),
    ("evaluation/define_evaluation_metrics.ipynb", 9,
     ["relevancy_score_prompt = PromptTemplate(", "0.33 - Somewhat relevant", "Final Score: [Average of all scores]",
      "ratio_of_relevant_docs_chain = ratio_of_relevant_docs_prompt | llm"]),
    ("evaluation/define_evaluation_metrics.ipynb", 10, ["def evaluate_ratio_of_relevant_docs(question, contexts)"]),
    ("evaluation/evaluation_deep_eval.ipynb", 2, ["GEval(", 'name="Correctness"']),
    ("evaluation/evaluation_deep_eval.ipynb", 4, ["FaithfulnessMetric("]),
    ("evaluation/evaluation_deep_eval.ipynb", 6, ["ContextualRelevancyMetric("]),
    ("evaluation/end-2-end_rag_evaluation.ipynb", 12, ["Is the answer complete?", "COMPLETE = 1"]),
    ("evaluation/end-2-end_rag_evaluation.ipynb", 19, ["from ragas.metrics import faithfulness"]),
    ("evaluation/end-2-end_rag_evaluation.ipynb", 22, ["FACTUALITY_THRESHOLD", "classification_report("]),
    ("evaluation/evaluation_grouse.ipynb", 4, ["GroundedQAEvaluator", "meta_evaluate_pipeline"]),
    ("evaluation/evaluation_grouse.ipynb", 36, ["meta_evaluate_pipeline("]),
    ("evaluation/open-rag-eval-example.ipynb", 7, ["UMBRELA", 'NO_RELEVANCE = "0"', 'EXACT_ANSWER = "3"']),
    ("evaluation/open-rag-eval-example.ipynb", 8, ["umbrela_scores"]),
    ("all_rag_techniques/choose_chunk_size.ipynb", 8, ["FaithfulnessEvaluator()", "RelevancyEvaluator()"]),
    ("all_rag_techniques/choose_chunk_size.ipynb", 10,
     ["similarity_top_k=5", "average_faithfulness", "average_relevancy", "average_response_time"]),
    ("all_rag_techniques/HyPE_Hypothetical_Prompt_Embeddings.ipynb", 0, ["improvement in retrieval precision"]),
]
for nb, i, needles in CELLS:
    src = cell(nb, i)
    for n in needles:
        check(n in src, f"{nb} cell {i}: {n}")
raw = open(os.path.join(REPO, "evaluation/define_evaluation_metrics.ipynb"), encoding="utf-8").read()
check(raw.count("ratio_of_relevant_docs_prompt") == 1,
      "define_evaluation_metrics.ipynb: 'ratio_of_relevant_docs_prompt' appears once (used in cell 9, never defined)")
py = open(os.path.join(REPO, "evaluation/evalute_rag.py"), encoding="utf-8").read().splitlines()
LINES = {95: "def evaluate_rag(retriever, num_questions: int = 5)", 117: "Rate on a scale of 1-5",
         134: "Generate {num_questions} diverse test questions", 144: "retriever.get_relevant_documents(question)",
         145: '"\\n".join([doc.page_content for doc in context])', 160: "def calculate_average_scores",
         163: "pass"}
for n, needle in LINES.items():
    check(needle in py[n - 1], f"evaluation/evalute_rag.py:L{n}: {needle}")

# ------------------------------------------------------------------ 3. book pages
print("\n=== B1 book pages (short phrases, each < 15 words)")


def page(chapter_file, p):
    d = fitz.open(os.path.join(BOOK, chapter_file))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


PAGES = [
    ("chapter 22.pdf", 4, 19, ["Precision at K measures what fraction of the top-K", "precision at five is 0.6",
                               "how much noise the retriever introduces"]),
    ("chapter 22.pdf", 5, 19, ["all relevant documents in the knowledge base", "recall is 0.3",
                               "context precision", "Ranking Quality: MRR, MAP, and NDCG"]),
    ("chapter 22.pdf", 6, 19, ["Mean Reciprocal Rank (MRR)", "position three, the score is 0.33",
                               "MRR is averaged across all test queries", "Mean Average Precision (MAP)",
                               "logarithmic discount", "normalizes against the ideal ranking",
                               "handles graded relevance", "ranges from zero to one"]),
    ("chapter 22.pdf", 7, 19, ["Ranking quality depends on where relevant documents appear"]),
    ("chapter 22.pdf", 8, 19, ["isolates generation quality from retrieval quality"]),
    ("chapter 22.pdf", 18, 19, ["Ranking metrics like MRR, MAP, and NDCG"]),
    ("Appendix.pdf", 13, 23, ["Appendix B: Glossary"]),
    ("Appendix.pdf", 15, 23, ["Context Precision A retrieval metric that accounts for ranking order"]),
    ("Appendix.pdf", 18, 23, ["MAP (Mean Average Precision)"]),
    ("Appendix.pdf", 19, 23, ["MRR (Mean Reciprocal Rank)", "NDCG (Normalized Discounted Cumulative Gain)",
                              "Precision at K A retrieval metric"]),
    ("Appendix.pdf", 20, 23, ["Recall at K A retrieval metric"]),
]
for f, p, total, needles in PAGES:
    t, n = page(f, p)
    check(n == total, f"{f} has {n} pages (cite as p.{p}/{total})")
    for s in needles:
        assert len(s.split()) < 15, s
        check(s in t, f"{f} p.{p}/{total}: {s}")

# whole-book absence checks
ABSENT = {"hit rate / Hit@": r"hit rate|hit@|hits@", "qrels": r"\bqrels?\b", "log2 / log base": r"log2|log_2|log base",
          "2^ gain": r"2\^", "DCG formula sign": r"DCG\s*="}
found = {k: [] for k in ABSENT}
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    d = fitz.open(f)
    for i, pg in enumerate(d, 1):
        t = pg.get_text()
        for k, pat in ABSENT.items():
            if re.search(pat, t, re.I):
                found[k].append(f"{os.path.basename(f)} p.{i}/{len(d)}")
for k, v in found.items():
    check(not v, f"book never contains {k}: {v if v else 'none found'}")

print("\nALL PASS" if fails == 0 else f"\n{fails} FAIL(S)")
