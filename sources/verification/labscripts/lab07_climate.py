"""Item 7: climate PDF through the repo's encode_pdf splitting path (no embeddings), page metadata,
per-page vs concatenated splitting, page-break cuts, chars/token.
Run: python -I lab07_climate.py <path-to-Understanding_Climate_Change.pdf>
"""
import re
import statistics as st
import sys
import importlib.metadata as md

import fitz  # PyMuPDF
import tiktoken
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

pdf = sys.argv[1]
print({p: md.version(p) for p in ("langchain-community", "langchain-text-splitters", "pypdf", "pymupdf", "tiktoken")})

# --- load exactly as helper_functions.encode_pdf L62-L63
docs = PyPDFLoader(pdf).load()
print("\nPyPDFLoader pages (Documents):", len(docs))
print("first doc metadata:", docs[0].metadata)
print("last doc metadata page/page_label:", docs[-1].metadata.get("page"), docs[-1].metadata.get("page_label"))
print("empty pages:", [d.metadata["page"] for d in docs if not d.page_content.strip()])

# --- split exactly as helper_functions.encode_pdf L66-L69
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
chunks = splitter.split_documents(docs)
lens = [len(c.page_content) for c in chunks]
print(f"\nper-page split_documents(1000,200,len): {len(chunks)} chunks; len min/median/max = "
      f"{min(lens)}/{st.median(lens)}/{max(lens)}; chunks < 200 chars = {sum(l < 200 for l in lens)}")
print("chunk metadata keys:", sorted(chunks[0].metadata.keys()))
print("any chunk metadata with >1 page: impossible by construction; distinct pages in chunks:",
      len({c.metadata['page'] for c in chunks}))
tabs = sum("\t" in c.page_content for c in chunks)
print("chunks containing a tab (what replace_t_with_space L18-L31 would change):", tabs)

# --- concatenated full text (page break -> "\n")
full = "\n".join(d.page_content for d in docs)
page_starts, pos = [], 0
for d in docs:
    page_starts.append(pos)
    pos += len(d.page_content) + 1
cross = splitter.create_documents([full])
cl = [len(c.page_content) for c in cross]
print(f"\nconcatenated split (same splitter): {len(cross)} chunks; len min/median/max = "
      f"{min(cl)}/{st.median(cl)}/{max(cl)}")
sp_idx = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len,
                                        add_start_index=True).create_documents([full])
import bisect
spanning = 0
for c in sp_idx:
    s = c.metadata["start_index"]
    e = s + len(c.page_content) - 1
    if bisect.bisect_right(page_starts, s) != bisect.bisect_right(page_starts, e):
        spanning += 1
print("concatenated chunks that span a page break:", spanning)

# --- page breaks that cut a sentence
print("\nPage breaks where page N does not end with terminal punctuation (possible mid-sentence cut):")
cuts = []
for i in range(len(docs) - 1):
    a = docs[i].page_content.rstrip()
    b = docs[i + 1].page_content.lstrip()
    if a and not re.search(r'[.!?:"”)]$', a):
        cuts.append(i)
        print(f"  page(meta) {docs[i].metadata['page']} -> {docs[i+1].metadata['page']}:"
              f"\n    END   ...{a[-80:]!r}\n    START {b[:80]!r}...")
print("count:", len(cuts), "of", len(docs) - 1, "page breaks")

# --- chars per token
text_pypdf = full
text_fitz = "\n".join(p.get_text() for p in fitz.open(pdf))
for name in ("cl100k_base", "gpt2"):
    enc = tiktoken.get_encoding(name)
    for label, t in (("PyPDFLoader", text_pypdf), ("PyMuPDF", text_fitz)):
        n = len(enc.encode(t))
        print(f"{name:12s} {label:11s}: chars={len(t)} tokens={n} chars/token={len(t)/n:.3f}")

enc = tiktoken.get_encoding("cl100k_base")
tl = [len(enc.encode(c.page_content)) for c in chunks]
print(f"\nper-page 1000/200 chunks, cl100k tokens: min/median/max = {min(tl)}/{st.median(tl)}/{max(tl)}; "
      f"> 256 tokens: {sum(t > 256 for t in tl)}/{len(tl)}; > 512 tokens: {sum(t > 512 for t in tl)}/{len(tl)}")
g2 = tiktoken.get_encoding("gpt2")
tg = [len(g2.encode(c.page_content)) for c in chunks]
print(f"per-page 1000/200 chunks, gpt2 tokens: min/median/max = {min(tg)}/{st.median(tg)}/{max(tg)}; "
      f"> 256: {sum(t > 256 for t in tg)}; > 512: {sum(t > 512 for t in tg)}")

# --- repeated lines across pages (headers/footers?)
from collections import Counter
lines = Counter()
for d in docs:
    for ln in {l.strip() for l in d.page_content.splitlines() if l.strip()}:
        lines[ln] += 1
print("\nlines appearing on >= 3 pages:", [(l, c) for l, c in lines.most_common(10) if c >= 3])
