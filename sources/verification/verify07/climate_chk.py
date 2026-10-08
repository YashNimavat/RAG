import sys, re
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
docs = PyPDFLoader(sys.argv[1]).load()
sp = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
ch = sp.split_documents(docs)
for i in (0,35,36):
    c=ch[i]; t=c.page_content
    print(i, "page", c.metadata["page"], "len", len(t)); print("  START", repr(t[:110])); print("  END", repr(t[-110:]))
t0=ch[0].page_content
m=re.search(r"[^.]*650,000[^.]*\.", t0); print("glacial sentence len", len(m.group(0).strip()), repr(m.group(0).strip()))
print("Chapter 2 on page1?", "Chapter 2: Causes" in docs[0].page_content, "page idx with Chapter 2:", [d.metadata["page"] for d in docs if "Chapter 2: Causes" in d.page_content])
print("PPP whole in any per-page chunk:", sum("leverage" in c.page_content and "large-scale climate solutions" in c.page_content for c in ch))
