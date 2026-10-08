"""Item 5 follow-up: what choose_chunk_size actually indexes, and whether the notebook / script chunking paths
run, using MockLLM + MockEmbedding (no API calls). Reads the repo data dir read-only.
Run: python -I lab05b_choose_chunk_size_paths.py <repo>/data
"""
import sys
import warnings
import importlib.metadata as md

from llama_index.core import SimpleDirectoryReader, Settings, VectorStoreIndex
from llama_index.core.llms import MockLLM
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.utils import get_tokenizer

print({p: md.version(p) for p in ("llama-index-core", "llama-index-readers-file")})
data_dir = sys.argv[1]
documents = SimpleDirectoryReader(data_dir).load_data()
from collections import Counter
print("SimpleDirectoryReader(data) -> documents:", len(documents))
print("documents per file:", dict(Counter(d.metadata.get("file_name") for d in documents)))
print("documents[0:20] (file_name, page_label):",
      [(d.metadata.get("file_name"), d.metadata.get("page_label")) for d in documents[0:20]])

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    from llama_index.core.evaluation import DatasetGenerator  # noqa: F401
    print("DatasetGenerator import OK; warnings at import:", [str(x.message)[:120] for x in w])

Settings.llm = MockLLM()
Settings.embed_model = MockEmbedding(embed_dim=8)
tok = get_tokenizer()
eval_documents = documents[0:20]

# Notebook path (choose_chunk_size.ipynb cell 10): Settings.chunk_size then Settings.chunk_overlap = size // 5
for cs in (128, 256):
    Settings.chunk_size = cs
    Settings.chunk_overlap = cs // 5
    idx = VectorStoreIndex.from_documents(eval_documents)
    nodes = list(idx.docstore.docs.values())
    tl = [len(tok(n.get_content())) for n in nodes]
    cl = [len(n.get_content()) for n in nodes]
    print(f"notebook path chunk_size={cs} overlap={cs//5}: {len(nodes)} nodes; tokens max={max(tl)}; "
          f"chars min/max={min(cl)}/{max(cl)}")

# Script path (choose_chunk_size.py L48): SentenceSplitter(chunk_size=chunk_size) -> default overlap
for cs in (128, 256):
    try:
        splitter = SentenceSplitter(chunk_size=cs)
        idx = VectorStoreIndex.from_documents(eval_documents, transformations=[splitter])
        print(f"script path chunk_size={cs}: OK, overlap={splitter.chunk_overlap}, nodes={len(idx.docstore.docs)}")
    except Exception as ex:  # noqa: BLE001
        print(f"script path chunk_size={cs}: {type(ex).__name__}: {ex}")
