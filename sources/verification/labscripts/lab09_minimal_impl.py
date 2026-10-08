"""Item 9: run the minimal chunkers (chunklib.py) on the climate PDF text and check properties.
Run: python -I lab09_minimal_impl.py <path-to-Understanding_Climate_Change.pdf>
"""
import os
import random
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunklib import (fixed_window_chunks, recursive_chunks, page_aware_chunks, join_pages,  # noqa: E402
                      check_chunks, chunks_containing)
from langchain_community.document_loaders import PyPDFLoader  # noqa: E402

pdf = sys.argv[1]
# Same page texts as helper_functions.encode_pdf (PyPDFLoader), 1-based page = list index + 1.
pages = [d.page_content for d in PyPDFLoader(pdf).load()]
full, starts = join_pages(pages)
print(f"pages={len(pages)} full_len={len(full)}")

for name, fn in (("fixed_window_chunks", fixed_window_chunks), ("recursive_chunks", recursive_chunks)):
    ch = fn(full, 1000, 200)
    check_chunks(full, ch, 1000)
    lens = [len(c.text) for c in ch]
    print(f"{name}(1000,200) on concatenated text: {len(ch)} chunks, len min/median/max="
          f"{min(lens)}/{st.median(lens)}/{max(lens)}  -> property checks PASSED")

# Randomised property test over many (size, overlap) settings
rng = random.Random(0)
n = 0
for _ in range(60):
    size = rng.randint(20, 3000)
    ov = rng.randint(0, size - 1)
    for fn in (fixed_window_chunks, recursive_chunks):
        check_chunks(full, fn(full, size, ov), size)
        n += 1
print(f"randomised property checks: {n} (chunker, size, overlap) combinations PASSED (seed 0)")

# Edge cases
for t in ("", "a", "abc", "x" * 23):
    for fn in (fixed_window_chunks, recursive_chunks):
        out = fn(t, 5, 2)
        if t:
            check_chunks(t, out, 5)
        print(f"  {fn.__name__}({t!r:.12}, 5, 2) -> {[(c.char_start, c.char_end, c.text) for c in out]}")
for bad in ((10, 10), (10, 11), (10, -1)):
    try:
        fixed_window_chunks("abc", *bad)
    except ValueError as e:
        print(f"  fixed_window_chunks('abc', size={bad[0]}, overlap={bad[1]}) -> ValueError: {e}")

# Page-aware chunking
pa = page_aware_chunks(pages, 1000, 200)
check_chunks(full, pa, 1000)
multi = [c for c in pa if c.page_start != c.page_end]
pp = sum(len(recursive_chunks(p, 1000, 200)) for p in pages)
print(f"\nrecursive_chunks(1000,200) applied per page (like encode_pdf): {pp} chunks")
print(f"page_aware_chunks(1000,200): {len(pa)} chunks; spanning 2+ pages: {len(multi)}; "
      f"first 3 (id, page_start, page_end): {[(c.chunk_id, c.page_start, c.page_end) for c in pa[:3]]}")

# A sentence cut by a page break: present whole in a page-aware chunk, never whole in per-page chunks.
SENT_A = "can leverage resources, expertise, and innovation to implement"
SENT_B = "large-scale climate solutions."
i = full.rfind("Public-", 0, full.index(SENT_A))
j = full.index(SENT_B, i) + len(SENT_B)
print(f"\ncut sentence span [{i},{j}) pages {starts and __import__('bisect').bisect_right(starts, i)}"
      f"-{__import__('bisect').bisect_right(starts, j - 1)} (1-based)")
print("  text:", repr(full[i:j]))
print("  page-aware chunks wholly containing it:", chunks_containing(pa, i, j))
per_page_hits = 0
for pno, ptxt in enumerate(pages, start=1):
    for c in recursive_chunks(ptxt, 1000, 200):
        if SENT_A in c.text and SENT_B in c.text:
            per_page_hits += 1
print("  per-page recursive chunks containing both halves:", per_page_hits)

from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
lc = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len).split_documents(
    [Document(page_content=p, metadata={"page": k}) for k, p in enumerate(pages)])
print("  LangChain per-page chunks containing both halves:",
      sum(SENT_A in c.page_content and SENT_B in c.page_content for c in lc), f"(of {len(lc)} chunks)")

print("\nLangChain on 'x'*23 with chunk_size=5, chunk_overlap=2:",
      RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=2).split_text("x" * 23))
