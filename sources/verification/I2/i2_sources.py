"""I2: check every repo-cell, repo-line and interview-repo citation the I2 lesson uses.

Read-only. Cells are 0-based. The upstream files are the raw files at commit 009adba (downloaded from
raw.githubusercontent.com in the cloud session, because the full clone was not present); the AIQ file is at e080df2.
Book pages are NOT checked here: the book PDFs were not present in this session (see I2_FACTS §0).
Run from rag_learning/:
    uv run python sources/verification/I2/i2_sources.py <dir with the upstream files> <dir with aiq/questions.md and aiq/LICENSE>
Saved output: sources/verification/I2/out_i2_sources.txt
"""
import hashlib
import json
import os
import re
import sys

REPO, AIQ = sys.argv[1], sys.argv[2]
fails = 0


def check(ok, label):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


def cell(nb, i):
    return "".join(json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]["source"])


CELLS = [
    ("all_rag_techniques/simple_rag.ipynb", 10,
     ["def encode_pdf(path, chunk_size=1000, chunk_overlap=200):", "PyPDFLoader(path)",
      "RecursiveCharacterTextSplitter(", "chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len",
      "text_splitter.split_documents(documents)"]),
    ("all_rag_techniques/hierarchical_indices.ipynb", 11, ["PyPDFLoader", "summary"]),
]
for nb, i, needles in CELLS:
    src = cell(nb, i)
    for n in needles:
        check(n in src, f"{nb} cell {i} contains {n!r}")
    check("separators" not in src, f"{nb} cell {i} passes no separators argument")

lines = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().split("\n")
check(lines[47].startswith("def encode_pdf("), f"helper_functions.py L48: {lines[47].strip()!r}")
check("return vectorstore" in lines[75], f"helper_functions.py L76: {lines[75].strip()!r}")
check(any("RecursiveCharacterTextSplitter(" in x for x in lines[47:76]), "helper_functions.py L48-L76 uses RecursiveCharacterTextSplitter")
hier = cell("all_rag_techniques/hierarchical_indices.ipynb", 11)
check("for page in" in hier or "documents" in hier, "hierarchical_indices.ipynb cell 11 summarises per PyPDFLoader page")
print("  cell 11 first lines:", " | ".join(x.strip() for x in hier.split("\n")[:6] if x.strip()))

readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read().lower()
for term in ("structure-aware", "markdownheader", "markdown header", "heading-aware", "header-aware"):
    check(term not in readme, f"README has no {term!r}")

pdf = os.path.join(REPO, "data", "Understanding_Climate_Change.pdf")
if os.path.exists(pdf):
    check(hashlib.sha256(open(pdf, "rb").read()).hexdigest().startswith("1d58a0fa"), "climate PDF sha256 1d58a0fa…")

q = open(os.path.join(AIQ, "questions.md"), encoding="utf-8").read()
lic = open(os.path.join(AIQ, "LICENSE"), encoding="utf-8").read()
check("MIT License" in lic and "Copyright (c) 2026 Om" in lic, "AIQ LICENSE: MIT, Copyright (c) 2026 Om")
check("### 4. What chunking strategies do you know, and how do you pick one?" in q, "AIQ 04 Q4 title")
check("Best choice whenever structure exists; the heading path alone fixes many retrieval misses." in q,
      "AIQ 04 Q4 structure-aware bullet (the overclaim, I2-E8)")
check("### 14. What metadata would you attach to each chunk, and what does it buy you?" in q, "AIQ 04 Q14 title")
check("### 13. How would you detect that a parser silently corrupted documents" in q, "AIQ 04 Q13 title")
m = re.search(r"### 4\. What chunking.*?</details>", q, re.S)
print(f"  AIQ Q4 block: {len(m.group(0))} characters")
print(f"\n{'ALL PASS' if not fails else f'{fails} FAIL'}")
sys.exit(1 if fails else 0)
