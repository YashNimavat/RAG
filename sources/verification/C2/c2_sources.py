"""C2: check every repo-cell, repo-line and book-page citation used by the C2 HTML lesson against the files.

Read-only on both sources. Cells are 0-based; book pages are 1-based PDF pages of the split chapter files.
Prints PASS/FAIL and match counts only: no book text is written to the output (copyright).
Run from rag_learning/:
    uv run python sources/verification/C2/c2_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/C2/out_c2_sources.txt
"""
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
    ("all_rag_techniques/simple_rag.ipynb", 10, ["def encode_pdf(path, chunk_size=1000, chunk_overlap=200)", "PyPDFLoader(path)",
                                                 "RecursiveCharacterTextSplitter(", "length_function=len", "split_documents(documents)",
                                                 "replace_t_with_space(texts)"]),
    ("all_rag_techniques/simple_rag.ipynb", 11, ["chunk_size=1000", "chunk_overlap=200"]),
    ("all_rag_techniques/simple_rag.ipynb", 13, ['"k": 2']),
    ("all_rag_techniques/context_enrichment_window_around_chunk.ipynb", 13, ["def split_text_to_chunks_with_indices(", "chunk_size - chunk_overlap"]),
    ("all_rag_techniques/proposition_chunking.ipynb", 9, ["from_tiktoken_encoder(", "chunk_size=200", "chunk_overlap=50"]),
    ("all_rag_techniques/reliable_rag.ipynb", 6, ["from_tiktoken_encoder(", "chunk_size=500", "chunk_overlap=0", "embed-english-v3.0"]),
    ("all_rag_techniques/document_augmentation.ipynb", 6, ["def split_document(", r"\b\w+\b"]),
    ("all_rag_techniques/choose_chunk_size.ipynb", 10, ["Settings.chunk_size = chunk_size", "chunk_size // 5", "similarity_top_k=5"]),
]
for nb, i, needles in CELLS:
    src = cell(nb, i)
    missing = [n for n in needles if n not in src]
    check(not missing, f"{nb} cell {i}: {len(needles) - len(missing)}/{len(needles)} needles" + (f" missing {missing}" if missing else ""))

for nb, i, needles in [("all_rag_techniques/proposition_chunking.ipynb", 9, ["langchain.text_splitter"]),
                       ("all_rag_techniques/reliable_rag.ipynb", 6, ["langchain.text_splitter"])]:
    check(all(n in cell(nb, i) for n in needles), f"{nb} cell {i}: imports from the pre-1.0 path langchain.text_splitter")

# context_enrichment cell 13: no validation of 0 <= overlap < size, and the whole text stored in each chunk's metadata
src = cell("all_rag_techniques/context_enrichment_window_around_chunk.ipynb", 13)
check("raise" not in src and "ValueError" not in src, "context_enrichment cell 13: no overlap/size validation (no raise)")
check(re.search(r"metadata\s*=\s*\{[^}]*\btext\b", src) is not None or "\"text\": text" in src or "'text': text" in src,
      "context_enrichment cell 13: stores the whole text in metadata")

lines = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
blk = "\n".join(lines[47:76])
for n in ("def encode_pdf(path, chunk_size=1000, chunk_overlap=200)", "PyPDFLoader(path)", "RecursiveCharacterTextSplitter(",
          "length_function=len", "split_documents(documents)", "replace_t_with_space(texts)", "OpenAIEmbeddings()", "FAISS.from_documents("):
    check(n in blk, f"helper_functions.py L48-L76 contains {n!r}")
check("OpenAIEmbeddings()" in lines[72], "helper_functions.py L73 = OpenAIEmbeddings()")
check("replace('\\t', ' ')" in "\n".join(lines[17:31]) or 'replace("\\t", " ")' in "\n".join(lines[17:31]),
      "helper_functions.py L18-L31 replace_t_with_space replaces tabs only")

# book pages: (file, 1-based page, number of pages in the file, regex, minimum matches)
PAGES = [
    ("chapter 1.pdf", 4, 14, r"1,000", 1), ("chapter 1.pdf", 4, 14, r"\b200\b", 1), ("chapter 1.pdf", 4, 14, r"overlap", 2),
    ("chapter 1.pdf", 5, 14, r"clean", 1), ("chapter 1.pdf", 5, 14, r"\btabs?\b", 1),
    ("chapter 1.pdf", 7, 14, r"\b1000\b", 1), ("chapter 1.pdf", 7, 14, r"\bclean\b", 1),
    ("chapter 1.pdf", 10, 14, r"most important", 1), ("chapter 1.pdf", 10, 14, r"\b100\b", 1),
    ("chapter 1.pdf", 11, 14, r"5,000", 1), ("chapter 1.pdf", 11, 14, r"just right", 1),
    ("chapter 1.pdf", 12, 14, r"overkill", 1), ("chapter 1.pdf", 13, 14, r"overlap", 1),
    ("Appendix.pdf", 14, 23, r"chunk overlap", 1), ("Appendix.pdf", 16, 23, r"fixed-size chunking", 1),
    ("chapter 4.pdf", 2, 15, r"blur", 1), ("chapter 7.pdf", 2, 11, r"pronoun", 1), ("chapter 7.pdf", 2, 11, r"heading", 1),
    ("chapter 8.pdf", 1, 11, r"partial", 1), ("chapter 8.pdf", 2, 11, r"character counter", 1),
    ("chapter 9.pdf", 2, 14, r"topic", 1),
]
for f, p, n, pat, k in PAGES:
    with fitz.open(os.path.join(BOOK, f)) as d:
        ok_n = len(d) == n
        t = " ".join(d[p - 1].get_text().split())
    m = len(re.findall(pat, t, re.I))
    check(ok_n and m >= k, f"{f} p.{p}/{n}: /{pat}/ x{m}")

# absence: the book never defines 'token' in its glossary (Appendix)
with fitz.open(os.path.join(BOOK, "Appendix.pdf")) as d:
    gl = " ".join(" ".join(d[i].get_text().split()) for i in range(12, 20))
check(re.search(r"\bToken\b\s*[:\-–]", gl) is None, "Appendix glossary pages 13-20: no 'Token' entry")

print(f"\n{'ALL PASS' if not fails else f'{fails} FAIL'}")
