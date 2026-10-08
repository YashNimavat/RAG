"""Hand-trace fixture for the lesson's code-tracing question (23-char string). Run: python -I lab09b_trace23.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunklib import fixed_window_chunks, recursive_chunks, check_chunks  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402

T = "abcdefghijklmnopqrstuvw"
print(len(T))
for size, ov in ((10, 3), (10, 0), (8, 4)):
    ch = fixed_window_chunks(T, size, ov)
    check_chunks(T, ch, size)
    print(f"fixed_window_chunks(T, {size}, {ov}) ->", [(c.char_start, c.char_end, c.text) for c in ch])
W = "the cat sat on the mat"
print(len(W))
print("recursive_chunks(W, 10, 4) ->", [(c.char_start, c.char_end, c.text) for c in recursive_chunks(W, 10, 4)])
print("LangChain(10, 4)            ->", RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=4).split_text(W))
