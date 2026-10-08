"""Items 4-6: LangChain RecursiveCharacterTextSplitter, LlamaIndex SentenceSplitter/Settings,
FaithfulnessEvaluator prompt keys. No network / API calls (MockLLM, MockEmbedding).
Run: python -I lab04_06_libs.py
"""
import inspect
import importlib.metadata as md

print({p: md.version(p) for p in ("langchain-text-splitters", "langchain-core", "llama-index-core", "tiktoken")})

# ---------------------------------------------------------------- Item 4
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters.base import TextSplitter

print("\n=== Item 4: RecursiveCharacterTextSplitter ===")
print("TextSplitter.__init__ signature:", inspect.signature(TextSplitter.__init__))
print("RecursiveCharacterTextSplitter.__init__ signature:",
      inspect.signature(RecursiveCharacterTextSplitter.__init__))
default = RecursiveCharacterTextSplitter()
print("default _separators:", default._separators)
print("default _chunk_size, _chunk_overlap:", default._chunk_size, default._chunk_overlap)
print("default _length_function is len:", default._length_function is len)

SAMPLE = (
    "Retrieval quality depends on what each vector represents. A chunk that mixes three topics "
    "produces an embedding that sits between them. A chunk that is too short loses the sentence "
    "that names its subject. Overlap repeats text across neighbouring chunks so that a boundary "
    "is less likely to cut a short fact in half. It does not guarantee anything for facts longer "
    "than the overlap itself."
)
print("\nSAMPLE length:", len(SAMPLE))
sp = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=40, length_function=len,
                                    add_start_index=True)
docs = sp.create_documents([SAMPLE])
prev_end = None
for i, d in enumerate(docs):
    s = d.metadata["start_index"]
    e = s + len(d.page_content)
    assert SAMPLE[s:e] == d.page_content
    ov = (prev_end - s) if prev_end is not None else None
    print(f"chunk {i}: [{s},{e}) len={len(d.page_content)} overlap_with_prev={ov} | {d.page_content!r}")
    prev_end = e

print("\nOverlap/size validation:")
for cs, co in ((100, 100), (100, 150), (100, 99), (100, -1)):
    try:
        RecursiveCharacterTextSplitter(chunk_size=cs, chunk_overlap=co)
        print(f"  chunk_size={cs} chunk_overlap={co}: OK (no exception)")
    except Exception as ex:  # noqa: BLE001
        print(f"  chunk_size={cs} chunk_overlap={co}: {type(ex).__name__}: {ex}")

print("\nOversized single word (no separator can split it) with chunk_size=10:")
sp2 = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=0)
print("  ", sp2.split_text("short " + "x" * 25 + " tail"))

# ---------------------------------------------------------------- Item 5
print("\n=== Item 5: LlamaIndex SentenceSplitter / Settings ===")
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings, Document
from llama_index.core.node_parser.text import sentence as sentence_mod
import llama_index.core.constants as C
from llama_index.core.utils import get_tokenizer

ss = SentenceSplitter()
print("SentenceSplitter() chunk_size, chunk_overlap:", ss.chunk_size, ss.chunk_overlap)
print("constants DEFAULT_CHUNK_SIZE:", C.DEFAULT_CHUNK_SIZE,
      " SENTENCE_CHUNK_OVERLAP:", getattr(sentence_mod, "SENTENCE_CHUNK_OVERLAP", "n/a"))
for cs in (128, 200, 201, 256):
    try:
        x = SentenceSplitter(chunk_size=cs)
        print(f"  SentenceSplitter(chunk_size={cs}): OK, chunk_overlap={x.chunk_overlap}")
    except Exception as ex:  # noqa: BLE001
        print(f"  SentenceSplitter(chunk_size={cs}): {type(ex).__name__}: {ex}")

tok = get_tokenizer()
print("default tokenizer:", tok)
try:
    print("  tokenizer.__self__ (encoding):", tok.__self__, getattr(tok.__self__, "name", None))
except AttributeError:
    pass
import tiktoken
probe = "Chunking splits a document into retrievable units."
print("  len(get_tokenizer()(probe)) =", len(tok(probe)),
      "| cl100k_base =", len(tiktoken.get_encoding("cl100k_base").encode(probe)),
      "| gpt2 =", len(tiktoken.get_encoding("gpt2").encode(probe)))

# Settings path used by the notebook (cell 10): Settings.chunk_size then Settings.chunk_overlap
print("\nSettings defaults: chunk_size =", Settings.chunk_size, " chunk_overlap =", Settings.chunk_overlap)
print("Settings.node_parser type:", type(Settings.node_parser).__name__)
try:
    Settings.chunk_size = 128
    print("Settings.chunk_size = 128 -> OK; node_parser.chunk_overlap now", Settings.node_parser.chunk_overlap)
except Exception as ex:  # noqa: BLE001
    print("Settings.chunk_size = 128 ->", type(ex).__name__, ex)
Settings.chunk_overlap = 128 // 5
print("Settings.chunk_overlap = 25 -> node_parser:", Settings.node_parser.chunk_size,
      Settings.node_parser.chunk_overlap)
# Do the parser's chunks respect the token limit, measured with its own tokenizer?
long_text = " ".join(f"Sentence number {i} talks about chunk boundaries and overlap." for i in range(200))
nodes = Settings.node_parser.get_nodes_from_documents([Document(text=long_text)])
lens = [len(tok(n.get_content())) for n in nodes]
print(f"Settings.node_parser on synthetic text: {len(nodes)} nodes, token lens min/max = {min(lens)}/{max(lens)}"
      f" (limit {Settings.node_parser.chunk_size}); char lens min/max = "
      f"{min(len(n.get_content()) for n in nodes)}/{max(len(n.get_content()) for n in nodes)}")

# ---------------------------------------------------------------- Item 6
print("\n=== Item 6: FaithfulnessEvaluator prompt keys ===")
from llama_index.core.llms import MockLLM
from llama_index.core.evaluation import FaithfulnessEvaluator
from llama_index.core.prompts import PromptTemplate

ev = FaithfulnessEvaluator(llm=MockLLM())
before = {k: v.get_template() for k, v in ev.get_prompts().items()}
print("get_prompts().keys():", list(before.keys()))
NEW = PromptTemplate("CUSTOM PROMPT Information: {query_str} Context: {context_str} Answer:")
ret = ev.update_prompts({"your_prompt_key": NEW})
after = {k: v.get_template() for k, v in ev.get_prompts().items()}
print("update_prompts({'your_prompt_key': ...}) returned:", ret, "| raised: no")
print("any template changed:", any(before[k] != after[k] for k in before))
print("any template contains 'CUSTOM PROMPT':", any("CUSTOM PROMPT" in t for t in after.values()))
# Positive control: the real key
ev.update_prompts({"eval_template": NEW})
after2 = {k: v.get_template() for k, v in ev.get_prompts().items()}
print("after update_prompts({'eval_template': ...}): eval_template changed =",
      after2["eval_template"] != before["eval_template"],
      "| contains CUSTOM PROMPT =", "CUSTOM PROMPT" in after2["eval_template"])
print("first 120 chars of default eval_template:", repr(before["eval_template"][:120]))
