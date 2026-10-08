import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF = sys.argv[1]
docs = PyPDFLoader(PDF).load()                                    # helper_functions.py:L62-L63
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200,
                                          length_function=len, add_start_index=True)  # L66-L68 + offsets
chunks = splitter.split_documents(docs)                           # L69: splits page by page
print(len(docs), len(chunks), docs[0].metadata["page"], docs[0].metadata["page_label"])
prev = None                                                       # (page, end offset) of the previous chunk
for c in chunks[:6]:
    page, s = c.metadata["page"], c.metadata["start_index"]
    e = s + len(c.page_content)
    overlap = prev[1] - s if prev and prev[0] == page else None   # None at a page start
    print(f"page={page} span=[{s},{e}) len={len(c.page_content)} overlap_with_prev={overlap}")
    prev = (page, e)
