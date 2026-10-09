"""P1: check every repo-cell and book-page citation in concepts/P1_llm_fundamentals.md against the files.

Read-only on both sources. Cells are 0-based. Book pages are 1-based PDF pages of the split chapter files.
Run from rag_learning/:
    uv run python sources/verification/P1/p1_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/P1/out_p1_sources.txt
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

# (notebook, 0-based cell, literal substrings that must all be in that cell)
CELLS = [
    ("all_rag_techniques/proposition_chunking.ipynb", 9, ["from_tiktoken_encoder(", "chunk_size=200, chunk_overlap=50"]),
    ("all_rag_techniques/reliable_rag.ipynb", 6, ["from_tiktoken_encoder(", "chunk_size=500, chunk_overlap=0"]),
    ("all_rag_techniques/contextual_chunk_headers.ipynb", 11,
     ["MAX_CONTENT_TOKENS = 4000", "tiktoken.encoding_for_model('gpt-3.5-turbo')", 'MODEL_NAME = "gpt-4o-mini"',
      "max_tokens=MAX_CONTENT_TOKENS", "temperature=0.2", "tokens[:max_tokens]", "num_words=3000"]),
    ("all_rag_techniques/simple_rag_with_llamaindex.ipynb", 4,
     ["langchain uses length of the string", "llamaindex uses length of the tokens", "CHUNK_SIZE = 200", "CHUNK_OVERLAP = 50"]),
    ("all_rag_techniques/simple_rag_with_llamaindex.ipynb", 13, ["SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)"]),
    ("all_rag_techniques/document_augmentation.ipynb", 4,
     ["DOCUMENT_MAX_TOKENS = 4000", "FRAGMENT_MAX_TOKENS = 128", "Llama 3.1 8B 128k"]),
    ("all_rag_techniques/document_augmentation.ipynb", 6,
     [r"re.findall(r'\b\w+\b', document)", "in terms of the number of tokens", 'ChatOpenAI(model="gpt-4o-mini", temperature=0)']),
    ("all_rag_techniques/simple_rag.ipynb", 10, ["chunk_size=1000", "length_function=len"]),
    ("all_rag_techniques/choose_chunk_size.ipynb", 8, ['OpenAI(temperature=0, model="gpt-4o")', "FaithfulnessEvaluator()"]),
    ("all_rag_techniques/reliable_rag.ipynb", 14, ['ChatGroq(model="llama-3.1-8b-instant", temperature=0)', "You are a grader"]),
    ("evaluation/define_evaluation_metrics.ipynb", 1, ['ChatOpenAI(temperature=0, model_name="gpt-4o", max_tokens=4000)']),
    ("all_rag_techniques/graph_rag.ipynb", 12, ["get_openai_callback() as cb", "cb.prompt_tokens", "cb.completion_tokens", "cb.total_cost"]),
]
for nb, i, needles in CELLS:
    src = "".join(json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]["source"])
    for n in needles:
        check(n in src, f"{nb} cell {i}: {n}")
src = "".join(json.load(open(os.path.join(REPO, "all_rag_techniques/graph_rag.ipynb"), encoding="utf-8"))["cells"][12]["source"])
check(src.count("max_context_length") == 1, "graph_rag.ipynb cell 12: max_context_length is set once and never read in that cell")


def page(chapter_file, p):
    d = fitz.open(os.path.join(BOOK, chapter_file))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


# (file, 1-based page, expected page count, phrase that must appear; phrases are < 15 words)
PAGES = [
    ("chapter 1.pdf", 12, 14, "context window"),
    ("chapter 2.pdf", 9, 11, "charged per token"),
    ("chapter 4.pdf", 5, 15, "exceeding its context window"),
    ("chapter 9.pdf", 9, 14, "context window"),
    ("chapter 10.pdf", 12, 13, "every token counts"),
    ("chapter 22.pdf", 8, 19, "different random seeds"),
    ("chapter 22.pdf", 14, 19, "input tokens from the context plus output tokens"),
    ("chapter 22.pdf", 18, 19, "token costs"),
]
for f, p, total, phrase in PAGES:
    t, n = page(f, p)
    check(n == total and phrase in t, f"Ch {f} p.{p}/{n}: '{phrase}'")

# Absences: "tokenize" appears only for BM25 word splitting (Ch12), and "temperature" never means sampling.
hits_tok, hits_temp = [], []
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    for k, pg in enumerate(fitz.open(f)):
        t = pg.get_text()
        hits_tok += [f"{os.path.basename(f)} p.{k+1}/{len(fitz.open(f))}" for _ in re.findall(r"tokeni[sz]", t, re.I)]
        hits_temp += [f"{os.path.basename(f)} p.{k+1}" for _ in re.findall(r"temperature", t, re.I)]
check(hits_tok == ["chapter 12.pdf p.6/14", "chapter 12.pdf p.10/14"],
      f"book: 'tokeniz' occurs only at {hits_tok} (BM25 splitting a query/chunk into words; no subword tokenizer)")
print(f"INFO book: 'temperature' occurrences = {len(hits_temp)} on {sorted(set(hits_temp))}"
      " (read by hand: all are about Earth's climate, none about sampling)")
print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAIL'}")
