"""C1: check every repo-cell, repo-line and book-page citation in concepts/C1_document_parsing.md.

Read-only on both sources. Cells are 0-based; lines are 1-based. Book pages are 1-based PDF pages of the split
chapter files. Every book phrase checked here is shorter than 15 words.
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C1/c1_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/C1/out_c1_sources.txt
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

# ---- helper_functions.py lines (1-based)
hf = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
LINES = [
    (1, "from langchain_community.document_loaders import PyPDFLoader"),
    (10, "import fitz"),
    (18, "def replace_t_with_space(list_of_documents):"),
    (30, "doc.page_content = doc.page_content.replace('\\t', ' ')"),
    (31, "return list_of_documents"),
    (48, "def encode_pdf(path, chunk_size=1000, chunk_overlap=200):"),
    (62, "loader = PyPDFLoader(path)"),
    (63, "documents = loader.load()"),
    (69, "texts = text_splitter.split_documents(documents)"),
    (70, "cleaned_texts = replace_t_with_space(texts)"),
    (76, "return vectorstore"),
    (223, "def read_pdf_to_string(path):"),
    (237, "doc = fitz.open(path)"),
    (238, 'content = ""'),
    (244, "content += page.get_text()"),
    (245, "return content"),
]
for n, needle in LINES:
    check(needle in hf[n - 1], f"helper_functions.py:L{n}: {needle}")

# ---- notebook cells (0-based)
CELLS = [
    ("all_rag_techniques/simple_rag.ipynb", 10,
     ["loader = PyPDFLoader(path)", "text_splitter.split_documents(documents)", "cleaned_texts = replace_t_with_space(texts)"]),
    ("all_rag_techniques/multi_model_rag_with_captioning.ipynb", 8, ["text_data = []", "img_data = []"]),
    ("all_rag_techniques/multi_model_rag_with_captioning.ipynb", 9,
     ["fitz.open('attention_is_all_you_need.pdf')", "text = page.get_text().strip()",
      '"name": page_number+1', "page.get_images(full=True)", "extract_image(xref)"]),
]
for nb, i, needles in CELLS:
    src = cell(nb, i)
    for n in needles:
        check(n in src, f"{nb} cell {i}: {n}")
check("get_text" not in cell("all_rag_techniques/multi_model_rag_with_captioning.ipynb", 8),
      "multi_model_rag_with_captioning.ipynb cell 8 only initialises two lists (no extraction)")
check(not glob.glob(os.path.join(REPO, "**", "attention_is_all_you_need.pdf"), recursive=True),
      "attention_is_all_you_need.pdf is NOT in the pinned repo (the notebook downloads it)")

# ---- repo-wide counts over code cells and .py files
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


for pat in (r"PyPDFLoader", r"read_pdf_to_string", r"SimpleDirectoryReader", r"fitz\.open", r"get_text\(",
            r"replace_t_with_space"):
    h = count(pat)
    print(f"INFO repo code matches for /{pat}/: {len(h)}: {h}")
for pat, label in ((r"(?i)hyphen", "de-hyphenation"), (r"(?i)ligature|unicodedata|NFKC", "ligature / Unicode normalisation"),
                   (r"(?i)footer|running header", "header/footer removal"), (r"find_tables", "PyMuPDF table detection")):
    check(len(count(pat)) == 0, f"repo code: no {label} anywhere (/{pat}/)")


# ---- book pages
def page(chapter_file, p):
    d = fitz.open(os.path.join(BOOK, chapter_file))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


PAGES = [
    ("chapter 1.pdf", 4, 14, "Step 1: Load the Document"),
    ("chapter 1.pdf", 4, 14, "PDF is parsed page by page"),
    ("chapter 1.pdf", 4, 14, "Poor text extraction leads to poor retrieval downstream"),
    ("chapter 1.pdf", 4, 14, "librarian transcribing a book onto index cards"),
    ("chapter 1.pdf", 4, 14, "Step 2: Split Into Chunks"),
    ("chapter 1.pdf", 5, 14, "Step 3: Clean the Text"),
    ("chapter 1.pdf", 5, 14, "stray tab characters, extra whitespace, broken line endings"),
    ("chapter 1.pdf", 5, 14, "Dirty text leads to noisy embeddings"),
    ("chapter 1.pdf", 7, 14, "Load document and extract raw text"),
    ("chapter 1.pdf", 7, 14, "Clean each chunk (remove formatting artifacts)"),
    ("chapter 1.pdf", 2, 14, "Without RAG, a robot answers from memory"),
    ("chapter 1.pdf", 13, 14, "Factor Impact Latency Low: one embedding call"),
    ("chapter 2.pdf", 4, 11, "Unlike a PDF, where you get one continuous stream of text"),
    ("chapter 3.pdf", 1, 14, "page footer stuffed with navigation links"),
    ("chapter 14.pdf", 5, 13, "is tagged with page 3"),
    ("chapter 16.pdf", 1, 11, "Standard RAG extracts text from documents and ignores everything else"),
    ("chapter 16.pdf", 4, 11, "Step 1: Extract Text and Images Separately"),
    ("chapter 16.pdf", 4, 11, "tagged with metadata noting which page it came from"),
    ("chapter 16.pdf", 5, 11, "dual extraction of content types"),
    ("chapter 16.pdf", 10, 11, "Tables are already extracted as structured text by the PDF parser"),
]
for f, p, total, phrase in PAGES:
    text, n = page(f, p)
    check(n == total and phrase in text, f"{f} p.{p}/{total}: '{phrase}' ({len(phrase.split())} words)")
    check(len(phrase.split()) < 15, f"   phrase under 15 words ({len(phrase.split())})")

# Order on Ch1: Split (Step 2, p.4) comes before Clean (Step 3, p.5); the p.7 sketch lists split as 2, clean as 3
t7, _ = page("chapter 1.pdf", 7)
check(t7.find("2. Split text into chunks") < t7.find("3. Clean each chunk"), "Ch1 p.7/14 sketch: split (2) before clean (3)")

# Absences across the whole book
alltext = []
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    for i, pg in enumerate(fitz.open(f), 1):
        alltext.append((os.path.basename(f), i, re.sub(r"\s+", " ", pg.get_text())))
for pat, label in ((r"(?i)hyphen", "hyphenation"), (r"(?i)ligature", "ligatures"), (r"\bOCR\b", "OCR"),
                   (r"(?i)two-column|multi-column|reading order", "two-column / reading order"),
                   (r"(?i)PyMuPDF|pypdf|fitz", "a named PDF library"), (r"(?i)scanned", "scanned pages"),
                   (r"(?i)snapshot", "a text snapshot")):
    hits = [f"{f} p.{i}" for f, i, t in alltext if re.search(pat, t)]
    print(f"INFO book pages matching /{pat}/: {hits}")
    check(not hits, f"book: no mention of {label}")
hits = [f"{f} p.{i}" for f, i, t in alltext if re.search(r"(?i)\bfooters?\b|\bheaders?\b", t)]
print(f"INFO book pages with 'header'/'footer': {hits}")

print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAIL'}")
