import sys; sys.path.insert(0, sys.argv[1])
from ragkit._core import join_pages
from ragkit.chunking import ChunkerConfig, chunk_document
PAGES = ["Heading\n\nFirst page text that ends mid-sentence because the page",
         "break came here. Second page continues.\n\nNew paragraph on page two."]
CUT = "because the page\nbreak came here."
print(len(CUT))
ch = chunk_document("doc1", PAGES, ChunkerConfig(name="recursive", size=60, overlap=30, scope="cross_page"))
print(any(CUT in c.text for c in ch), [c.text for c in ch])
