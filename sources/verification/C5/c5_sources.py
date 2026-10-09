"""C5: check every repo-cell and book-page citation in concepts/C5_generation_citations.md against the files.

Read-only on both sources. Cells are 0-based. Book pages are 1-based PDF pages of the split chapter files.
Book phrases checked here are short (each under 15 words); the lesson paraphrases them.
Also: installed groq SDK facts used by the lesson (signature and docstrings only; no API call, no .env).
Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C5/c5_sources.py "<Book RAG>/upstream/RAG_Techniques" "<Book RAG>/RAG_Made_Simple_The_Complete_Visual_Guide"
Saved output: sources/verification/C5/out_c5_sources.txt
"""
import glob
import inspect
import json
import os
import re
import subprocess
import sys
import typing

import pymupdf as fitz

REPO, BOOK = sys.argv[1], sys.argv[2]
fails = 0


def check(ok, label):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
check(head == "009adba2be1bef49780ef73b6dd3c18fd24b035b", f"repo HEAD {head}")


def nb(path):
    return json.load(open(os.path.join(REPO, path), encoding="utf-8"))["cells"]


def cell(path, i):
    c = nb(path)[i]
    return c["cell_type"], "".join(c["source"]), c.get("outputs", [])


T = "all_rag_techniques/"
CELLS = [
    # simple_rag: retrieval only
    (T + "simple_rag.ipynb", 13, ['search_kwargs={"k": 2}']),
    (T + "simple_rag.ipynb", 15, ["retrieve_context_per_question(test_query, chunks_query_retriever)", "show_context(context)"]),
    (T + "simple_rag.ipynb", 17, ["evaluate_rag(chunks_query_retriever)"]),
    # local_rag_huggingface_faiss: page-tagged context, answer parsing, "sources" = a second retrieval
    (T + "local_rag_huggingface_faiss.ipynb", 22, ["using ONLY the context provided below"]),
    (T + "local_rag_huggingface_faiss.ipynb", 24, ["[Page {doc.metadata.get('page', '?')}]", '"\\n\\n".join(']),
    (T + "local_rag_huggingface_faiss.ipynb", 26, ['raw.strip().split("Answer:")[-1].strip()', "What is the GDP of India in 2024?"]),
    (T + "local_rag_huggingface_faiss.ipynb", 28, ["RunnableParallel(", "answer=rag_chain,", "sources=retriever,", 'print("Sources used:")']),
    # crag: sources appended as text; the local document has no identifier
    (T + "crag.ipynb", 20, ["def generate_response(query: str, knowledge: str, sources: List[Tuple[str, str]]) -> str:",
                            "Include the sources with their links (if available) at the end of your answer",
                            "return [doc.page_content for doc in docs]"]),
    (T + "crag.ipynb", 22, ['sources.append(("Retrieved document", ""))', "response = generate_response(query, final_knowledge, sources)"]),
    # reliable_rag: generation + LLM source highlighting
    (T + "reliable_rag.ipynb", 18, ["Answer the question based upon your knowledge.", 'ChatGroq(model="llama-3.1-8b-instant", temperature=0)']),
    (T + "reliable_rag.ipynb", 22, ["PydanticOutputParser(pydantic_object=HighlightDocuments)", 'ChatGroq(model="mixtral-8x7b-32768", temperature=0)',
                                    "Each segment is an exact match to a part of the document",
                                    "If you didn't used the specific document don't mention it."]),
    (T + "reliable_rag.ipynb", 23, ["for id, title, source, segment in zip(lookup_response.id"]),
    # graph_rag_local_attribution: the only notebook that parses inline citations from an answer
    (T + "graph_rag_local_attribution.ipynb", 9, ["CRITICAL: Cite your sources using [N] notation for each claim.",
                                                  "citation_refs = re.findall(r'\\[(\\d+)\\]', answer_text)",
                                                  "for ref in set(citation_refs):", "if key in source_map:", "confidence=0.9,"]),
    (T + "graph_rag_local_attribution.ipynb", 19, ['print(f"\\n📚 Citations: {len(result.citations)} sources verified")']),
]
for path, i, needles in CELLS:
    kind, src, _ = cell(path, i)
    check(kind == "code", f"{path} cell {i} is a code cell")
    for n in needles:
        check(n in src, f"{path} cell {i}: {n}")

# saved outputs
for path, i in [(T + "local_rag_huggingface_faiss.ipynb", 26), (T + "local_rag_huggingface_faiss.ipynb", 28),
                (T + "graph_rag_local_attribution.ipynb", 9), (T + "graph_rag_local_attribution.ipynb", 17),
                (T + "graph_rag_local_attribution.ipynb", 19)]:
    check(len(cell(path, i)[2]) == 0, f"{path} cell {i}: no saved output (behaviour not shown)")
_, _, out = cell(T + "reliable_rag.ipynb", 23)
check("ID: doc3" in "".join("".join(o.get("text", "")) for o in out), "reliable_rag cell 23 saved output lists 'ID: doc3'")
check("Answer:" in cell(T + "local_rag_huggingface_faiss.ipynb", 22)[1], "local_rag cell 22 prompt ends with an 'Answer:' cue")
check(not re.search(r"\bcit(e|ation)", cell(T + "local_rag_huggingface_faiss.ipynb", 22)[1], re.I),
      "local_rag cell 22 prompt never asks for citations")

# graph_rag_local_attribution cell 9: the parse filters unknown keys with no else branch (silent drop)
src9 = cell(T + "graph_rag_local_attribution.ipynb", 9)[1]
blk = src9[src9.index("for ref in set(citation_refs):"):src9.index("# Build reasoning trace")]
check("if key in source_map:" in blk and "else" not in blk, "graph_rag_local_attribution cell 9: unknown [N] silently dropped (no else)")
check(cell(T + "graph_rag_local_attribution.ipynb", 0)[1].count("Ollama") >= 1, "graph_rag_local_attribution cell 0: runs on Ollama")

# simple_rag never calls an LLM to answer
sr = [("".join(c["source"])) for c in nb(T + "simple_rag.ipynb") if c["cell_type"] == "code"]
check(not any(re.search(r"Chat[A-Z]|\.invoke\(|llm\b", s) for s in sr), "simple_rag.ipynb: no code cell builds or invokes a chat model")
check(len(nb(T + "simple_rag.ipynb")) == 22, "simple_rag.ipynb has 22 cells")

# reliable_rag: nothing checks the highlighted segments against the documents
rr = [("".join(c["source"])) for c in nb(T + "reliable_rag.ipynb") if c["cell_type"] == "code"]
check(not any(re.search(r"segment\s+in\s+(?!zip\()|in\s+doc\.page_content|\.find\(segment", s) for s in rr),
      "reliable_rag.ipynb: no code checks a highlighted segment is really in a document")

# helper_functions.py L162-L205 (the context-only QA chain) has no citations
lines = open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read().splitlines()
check(lines[161].startswith("def create_question_answer_from_context_chain(llm):"), "helper_functions.py L162 def")
check(not any(re.search(r"\bcit(e|ation)|source", l, re.I) for l in lines[161:205]), "helper_functions.py L162-L205: no citation or source handling")

# repo-wide: which code parses citation tags out of a generated answer?
hits = []
for f in sorted(glob.glob(os.path.join(REPO, "**", "*.ipynb"), recursive=True)):
    for i, c in enumerate(json.load(open(f, encoding="utf-8"))["cells"]):
        s = "".join(c["source"])
        if c["cell_type"] == "code" and re.search(r"re\.findall\(r?['\"]\\\[", s):
            hits.append((os.path.relpath(f, REPO).replace("\\", "/"), i))
for f in sorted(glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True)):
    if re.search(r"re\.findall\(r?['\"]\\\[", open(f, encoding="utf-8", errors="ignore").read()):
        hits.append((os.path.relpath(f, REPO).replace("\\", "/"), "py"))
print("code that runs re.findall on a '[' pattern:", hits)
check(hits == [(T + "graph_rag_local_attribution.ipynb", 9)], "only graph_rag_local_attribution cell 9 parses [..] tags (repo-wide)")
gr = cell("evaluation/evaluation_grouse.ipynb", 30)[1]
check("All sentences in the answer cite their sources" in gr, "evaluation/evaluation_grouse.ipynb cell 30: citation rubric for a judge")

# ---------------------------------------------------------------- book
def page(f, p):
    d = fitz.open(os.path.join(BOOK, f))
    return re.sub(r"\s+", " ", d[p - 1].get_text()), len(d)


BOOKP = [  # (file, page, total, short phrase that must be on that page)
    ("chapter 1.pdf", 9, 14, "Step 8: Generate the Answer"),
    ("chapter 1.pdf", 9, 14, "not in its training memory"),
    ("chapter 1.pdf", 10, 14, "Pass question + retrieved chunks to the language model"),
    ("chapter 3.pdf", 6, 14, "Even with perfect context"),
    ("chapter 3.pdf", 6, 14, "Is this answer faithful to the chunks?"),
    ("chapter 3.pdf", 8, 14, "Step 5: Highlight Source Segments"),
    ("chapter 3.pdf", 8, 14, "verbatim excerpts from the source documents"),
    ("chapter 3.pdf", 8, 14, "adding footnotes to a research paper"),
    ("chapter 3.pdf", 9, 14, "Return segments with document IDs and source references"),
    ("chapter 3.pdf", 11, 14, "is better than a confident wrong answer"),
    ("chapter 19.pdf", 8, 10, "attribution works after generation"),
    ("chapter 19.pdf", 8, 10, "explains why each document was retrieved"),
    ("chapter 22.pdf", 7, 19, "Measuring Faithfulness"),
    ("chapter 22.pdf", 8, 19, "This metric isolates generation quality from retrieval quality."),
    ("chapter 22.pdf", 8, 19, "the problem is in the language model or the prompt"),
    ("Appendix.pdf", 5, 23, "requiring each claim to cite its source"),
    ("Appendix.pdf", 21, 23, "footnote-style citations"),
]
for f, p, tot, phrase in BOOKP:
    t, n = page(f, p)
    check(n == tot, f"{f} has {tot} pages")
    check(len(phrase.split()) < 15, f"phrase under 15 words: {phrase!r}")
    check(phrase in t, f"{f} p.{p}/{tot}: {phrase!r}")

allp = []
for f in sorted(glob.glob(os.path.join(BOOK, "*.pdf"))):
    d = fitz.open(f)
    allp += [(os.path.basename(f), i + 1, re.sub(r"\s+", " ", pg.get_text())) for i, pg in enumerate(d)]
dk = [(f, p) for f, p, t in allp if re.search(r"don.t know", t, re.I)]
print("pages with \"don't know\":", dk)
check(dk == [("chapter 3.pdf", 11)], "\"I don't know\" appears only at Ch3 p.11/14")
check(not any(re.search(r"abstain|abstention", t, re.I) for _, _, t in allp), "book: no 'abstain'/'abstention' anywhere")
check(not any(re.search(r"\[[a-z_]+:\d+\]", t) for _, _, t in allp), "book: no inline [doc:page]-style citation format anywhere")
ch19 = [t for f, p, t in allp if f == "chapter 19.pdf"]
check(not any(re.search(r"\bcite", t, re.I) for t in ch19), "Ch19 never says 'cite' (Appendix p.5/23 says Ch19 requires claims to cite)")

# ---------------------------------------------------------------- installed groq SDK (no API call)
import importlib.metadata as md  # noqa: E402

from groq.resources.chat.completions import Completions  # noqa: E402
from groq.types.chat.chat_completion import Choice  # noqa: E402
from groq.types.completion_usage import CompletionTokensDetails, CompletionUsage  # noqa: E402

check(md.version("groq") == "1.7.0", f"groq SDK version {md.version('groq')}")
sig = inspect.signature(Completions.create).parameters
check(all(k in sig for k in ("model", "messages", "temperature", "max_tokens", "max_completion_tokens", "reasoning_effort")),
      "create() accepts model, messages, temperature, max_tokens, max_completion_tokens, reasoning_effort")
doc = inspect.getsource(Completions.create)
check("max_tokens: Deprecated in favor of `max_completion_tokens`" in doc, "docstring: max_tokens deprecated in favour of max_completion_tokens")
check("openai/gpt-oss-20b and openai/gpt-oss-120b support 'low', 'medium', or 'high'" in doc and "'medium' is the default value" in doc,
      "docstring: gpt-oss reasoning_effort low/medium/high, default medium")
check(list(Choice.model_fields) == ["finish_reason", "index", "logprobs", "message"], "Choice fields: finish_reason, index, logprobs, message")
check("length" in str(Choice.model_fields["finish_reason"].annotation), "finish_reason Literal includes 'length'")
check("completion_tokens_details" in CompletionUsage.model_fields and "reasoning_tokens" in CompletionTokensDetails.model_fields,
      "usage.completion_tokens_details.reasoning_tokens exists (Optional)")
# Added 2026-10-09 (external-resources review §3a rows 4-5): who applies the 'medium' default, and which
# finish_reason values the SDK types allow (used by make_answer's length_stop / unexpected_finish_reason flags).
import groq  # noqa: E402

check(isinstance(sig["reasoning_effort"].default, groq.Omit),
      "create(): reasoning_effort defaults to the SDK's Omit sentinel (field not sent; the server applies its default)")
check(typing.get_args(Choice.model_fields["finish_reason"].annotation) == ("stop", "length", "tool_calls", "function_call"),
      "Choice.finish_reason Literal values: stop, length, tool_calls, function_call")

print("ALL PASS" if fails == 0 else f"{fails} FAIL(S)")
sys.exit(1 if fails else 0)
