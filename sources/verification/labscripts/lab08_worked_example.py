"""Item 8: original paragraph chunked by hand-checkable fixed windows and by LangChain recursive splitter.
Run: python -I lab08_worked_example.py   (chunklib.py must sit next to this file)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I removes the script dir from sys.path
from chunklib import fixed_window_chunks, recursive_chunks, check_chunks, chunks_containing  # noqa: E402

# Original text written for this lab (not from the book).
PARA = (
    "A bi-encoder turns a passage into one vector in three steps. First, a WordPiece tokenizer "
    "splits the text into subword tokens and adds the special [CLS] and [SEP] markers. Second, a "
    "small transformer reads the token sequence and produces one contextual vector per token. "
    "Third, a pooling layer averages those token vectors into a single fixed-size embedding, "
    "which is then scaled to unit length. Two passages are later compared by the cosine of their "
    "vectors. Because the model was trained on short inputs, its "
    "configuration caps the sequence at 256 tokens. Tokens beyond the cap are silently dropped "
    "before the transformer runs. A sentence placed at the end of a long chunk can therefore have "
    "no influence at all on the chunk's embedding, even though the chunk text still contains it."
)
FACT = "Tokens beyond the cap are silently dropped before the transformer runs."
QUERY = "What happens to tokens past an embedding model's sequence limit?"

fs = PARA.index(FACT)
fe = fs + len(FACT)
print(f"len(PARA)={len(PARA)}; FACT span=[{fs},{fe}) len={len(FACT)}")
print(f"QUERY: {QUERY}\n")

for size, ov in ((300, 0), (300, 60)):
    ch = fixed_window_chunks(PARA, size, ov)
    check_chunks(PARA, ch, size)
    print(f"--- fixed_window_chunks(size={size}, overlap={ov}): {len(ch)} chunks")
    for c in ch:
        print(f"[{c.chunk_id}] {c.char_start:>3}-{c.char_end:<3} {c.text!r}")
    print(f"chunks wholly containing FACT: {chunks_containing(ch, fs, fe)}\n")

ch = recursive_chunks(PARA, 300, 60)
check_chunks(PARA, ch, 300)
print(f"--- recursive_chunks(size=300, overlap=60) [our simplified version]: {len(ch)} chunks")
for c in ch:
    print(f"[{c.chunk_id}] {c.char_start:>3}-{c.char_end:<3} len={len(c.text)} {c.text!r}")
print(f"chunks wholly containing FACT: {chunks_containing(ch, fs, fe)}\n")

from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402
docs = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=60, length_function=len,
                                      add_start_index=True).create_documents([PARA])
print(f"--- LangChain RecursiveCharacterTextSplitter(300, 60, len): {len(docs)} chunks")
prev = None
for i, d in enumerate(docs):
    s = d.metadata["start_index"]
    e = s + len(d.page_content)
    print(f"[{i}] {s:>3}-{e:<3} len={len(d.page_content)} overlap_prev={None if prev is None else prev - s}"
          f" contains_FACT={FACT in d.page_content} {d.page_content!r}")
    prev = e
