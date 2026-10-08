"""Item 7/10 extension: count tokens with the embedding models' OWN WordPiece tokenizers (tokenizer.json
downloaded from Hugging Face; loaded with the `tokenizers` library, no torch) for the encode_pdf-style chunks.
Run: python -I lab10_wordpiece.py <climate.pdf> <minilm tokenizer.json> <bge tokenizer.json>
"""
import statistics as st
import sys
import importlib.metadata as md

from tokenizers import Tokenizer
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

pdf, tok_minilm, tok_bge = sys.argv[1:4]
print({p: md.version(p) for p in ("tokenizers", "tiktoken", "langchain-text-splitters")})
docs = PyPDFLoader(pdf).load()
full = "\n".join(d.page_content for d in docs)

for size in (1000, 1500, 2000):
    chunks = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=size // 5,
                                            length_function=len).split_documents(docs)
    print(f"\n-- per-page RecursiveCharacterTextSplitter({size},{size//5},len): {len(chunks)} chunks")
    for label, path, limit in (("all-MiniLM-L6-v2", tok_minilm, 256), ("bge-small-en-v1.5", tok_bge, 512)):
        tk = Tokenizer.from_file(path)
        tk.no_truncation()
        tk.no_padding()
        n = [len(tk.encode(c.page_content).ids) for c in chunks]  # includes [CLS] and [SEP]
        print(f"   {label:18s} WordPiece tokens (incl. CLS/SEP) min/median/max = {min(n)}/{st.median(n)}/{max(n)};"
              f" > 256: {sum(x > 256 for x in n)}; > 512: {sum(x > 512 for x in n)};"
              f" over this model's limit {limit}: {sum(x > limit for x in n)}")
    cl = tiktoken.get_encoding("cl100k_base")
    m = [len(cl.encode(c.page_content)) for c in chunks]
    print(f"   cl100k_base tokens min/median/max = {min(m)}/{st.median(m)}/{max(m)}; > 256: {sum(x > 256 for x in m)}")

words = full.split()
print(f"\nfull text: chars={len(full)} whitespace-separated words={len(words)} chars/word={len(full)/len(words):.2f}"
      f" mean word length={sum(map(len, words))/len(words):.2f}")
for label, path in (("all-MiniLM-L6-v2", tok_minilm), ("bge-small-en-v1.5", tok_bge)):
    tk = Tokenizer.from_file(path)
    print(f"{label}: tokenizer.json built-in truncation={tk.truncation} padding={tk.padding}")
    tk.no_truncation()
    tk.no_padding()
    n = len(tk.encode(full).ids) - 2
    print(f"\nfull text, {label} WordPiece: tokens={n} chars/token={len(full)/n:.3f}")
    enc = tk.encode("Tokens beyond the cap are silently dropped before the transformer runs.")
    print("   example tokens:", enc.tokens)
