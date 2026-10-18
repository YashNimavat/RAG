"""I-CMP: check every upstream cell, helper line and interview-repo text the I-CMP files cite (PASS/FAIL only).

Repo: NirDiamant/RAG_Techniques @ 009adba2be1bef49780ef73b6dd3c18fd24b035b (custom non-commercial licence; only
short substrings are checked, nothing is copied out). Cells are 0-based. Interview repo:
ombharatiya/AI-Engineer-Interview-Questions @ e080df2 (MIT, Copyright (c) 2026 Om).
The book is not checked here (not present when this was written): every book page in the I-CMP files is UNVERIFIED.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I-CMP/icmp_sources.py \\
        "C:/Yash/New-Work/Book RAG/upstream/RAG_Techniques" "C:/Yash/New-Work/Book RAG/upstream/AI-Engineer-Interview-Questions" \\
        > sources/verification/I-CMP/out_icmp_sources.txt
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

REPO, AIQ = Path(sys.argv[1]), Path(sys.argv[2])
NB = REPO / "all_rag_techniques"
fails = n = 0


def check(ok, label):
    global fails, n
    n += 1
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label)


def cell(nb, i):
    c = json.loads((NB / f"{nb}.ipynb").read_text(encoding="utf-8"))["cells"][i]
    return "".join(c["source"]), c


def has(nb, i, *subs):
    src, _ = cell(nb, i)
    for s in subs:
        check(s in src, f"{nb} cell {i} contains {s!r}")


pdf = REPO / "data" / "Understanding_Climate_Change.pdf"
check(hashlib.sha256(pdf.read_bytes()).hexdigest().startswith("1d58a0fac2435c2c"), "climate PDF sha256 1d58a0fa…")

# simple_rag: characters, 1000/200, k = 2
has("simple_rag", 10, "def encode_pdf(path, chunk_size=1000, chunk_overlap=200)", "RecursiveCharacterTextSplitter(",
    "length_function=len", "PyPDFLoader(path)")
has("simple_rag", 13, 'search_kwargs={"k": 2}')
helper = (REPO / "helper_functions.py").read_text(encoding="utf-8").splitlines()
check(helper[47].startswith("def encode_pdf"), "helper_functions.py L48 is def encode_pdf")
check("OpenAIEmbeddings()" in helper[72], "helper_functions.py L73 hardcodes OpenAIEmbeddings()")
check(helper[75].strip() == "return vectorstore", "helper_functions.py L76 returns the vector store")

# choose_chunk_size: the data folder, 20 docs, 25 questions, [128, 256], overlap size // 5, gpt-4o judge, gpt-3.5 answers
has("choose_chunk_size", 4, 'data_dir = "../data"', "SimpleDirectoryReader(data_dir).load_data()")
has("choose_chunk_size", 6, "num_eval_questions = 25", "documents[0:20]")
has("choose_chunk_size", 8, 'model="gpt-4o"', "Settings.llm = gpt4")
has("choose_chunk_size", 10, 'OpenAI(model="gpt-3.5-turbo")', "Settings.chunk_size = chunk_size", "Settings.chunk_overlap = chunk_size // 5")
has("choose_chunk_size", 12, "chunk_sizes = [128, 256]")

# semantic_chunking: one string, percentile 90, OpenAI embeddings, k = 2
has("semantic_chunking", 10, "read_pdf_to_string(path)")
has("semantic_chunking", 12, "SemanticChunker(OpenAIEmbeddings()", "breakpoint_threshold_type='percentile'", "breakpoint_threshold_amount=90")
src12, _ = cell("semantic_chunking", 12)
check("max_chunk" not in src12 and "chunk_size" not in src12, "semantic_chunking cell 12 sets no size cap")
has("semantic_chunking", 14, "create_documents([content])")
has("semantic_chunking", 16, 'search_kwargs={"k": 2}')

# proposition_chunking: inline essay, gpt2 tiktoken 200/50, Ollama nomic, Groq llama-3.1-70b generates and grades, 7/10 thresholds
has("proposition_chunking", 7, "Paul Graham", 'sample_content = """')
has("proposition_chunking", 9, "from_tiktoken_encoder(", "chunk_size=200, chunk_overlap=50", "nomic-embed-text:v1.5")
has("proposition_chunking", 12, 'ChatGroq(model="llama-3.1-70b-versatile", temperature=0)')
has("proposition_chunking", 15, 'ChatGroq(model="llama-3.1-70b-versatile", temperature=0)', "accuracy", "conciseness")
has("proposition_chunking", 16, '"accuracy": 7, "clarity": 7, "completeness": 7, "conciseness": 7')

# contextual_chunk_headers: Nike 10-K text, 800/0 characters, gpt-4o-mini title from the first 4,000 tokens, Cohere rerank, KITE claims
has("contextual_chunk_headers", 8, "nike_2023_annual_report.txt")
has("contextual_chunk_headers", 9, "chunk_size: int = 800", "chunk_overlap=0", "length_function=len")
has("contextual_chunk_headers", 11, "MAX_CONTENT_TOKENS = 4000", 'MODEL_NAME = "gpt-4o-mini"')
has("contextual_chunk_headers", 13, 'MODEL = "rerank-english-v3.0"')
has("contextual_chunk_headers", 15, "KITE", "4 datasets and a total of 50 questions")
src15, _ = cell("contextual_chunk_headers", 15)
check("4.72" in src15 and "6.04" in src15, "contextual_chunk_headers cell 15 reports 4.72 -> 6.04 (repo claim)")

# document_augmentation: regex-word windows, question levels, k = 1
src4, _ = cell("document_augmentation", 4)
check("DOCUMENT_LEVEL = 1" in src4 and "FRAGMENT_LEVEL = 2" in src4, "document_augmentation cell 4 defines DOCUMENT_LEVEL / FRAGMENT_LEVEL")
for k, v in (("DOCUMENT_MAX_TOKENS", "4000"), ("DOCUMENT_OVERLAP_TOKENS", "100"), ("FRAGMENT_MAX_TOKENS", "128"),
             ("FRAGMENT_OVERLAP_TOKENS", "16"), ("QUESTIONS_PER_DOCUMENT", "40")):
    check(f"{k} = {v}" in src4, f"document_augmentation cell 4 sets {k} = {v}")
check("QUESTION_GENERATION = QuestionGeneration.DOCUMENT_LEVEL" in src4, "document_augmentation cell 4 uses DOCUMENT_LEVEL")
src6, _ = cell("document_augmentation", 6)
check("def split_document" in src6 and "re.findall(r'\\b\\w+\\b'" in src6, "document_augmentation cell 6 split_document counts regex words")
has("document_augmentation", 10, "split_document(content, DOCUMENT_MAX_TOKENS, DOCUMENT_OVERLAP_TOKENS)")
src10, _ = cell("document_augmentation", 10)
check('search_kwargs={"k": 1}' in src10, "document_augmentation cell 10 retrieves k = 1")
has("document_augmentation", 13, "read_pdf_to_string(path)")

# HyPE: 1000/200 characters, text-embedding-3-small, gpt-4o-mini, 97/97 saved output, cell 11 SyntaxError, k = 3 dedup by set
has("HyPE_Hypothetical_Prompt_Embeddings", 7, 'LANGUAGE_MODEL_NAME = "gpt-4o-mini"', 'EMBEDDING_MODEL_NAME = "text-embedding-3-small"',
    "CHUNK_SIZE = 1000", "CHUNK_OVERLAP = 200")
has("HyPE_Hypothetical_Prompt_Embeddings", 9, "temperature=0", "generate essential questions")
src11, _ = cell("HyPE_Hypothetical_Prompt_Embeddings", 11)
try:
    ast.parse(src11)
    syn = False
except SyntaxError:
    syn = True
check(syn, "HyPE cell 11 does not parse (SyntaxError as committed)")
_, c15 = cell("HyPE_Hypothetical_Prompt_Embeddings", 15)
out = "".join("".join(o.get("text", "")) for o in c15.get("outputs", []))
check("97/97" in out, "HyPE cell 15 saved output shows 97/97 chunks processed")
allsrc = "".join("".join(c["source"]) for c in json.loads((NB / "HyPE_Hypothetical_Prompt_Embeddings.ipynb").read_text(encoding="utf-8"))["cells"])
check('search_kwargs={"k": 3}' in allsrc and "set(" in allsrc, "HyPE retrieves k = 3 and deduplicates with set()")

# Interview repo: AIQ 04 Q4 (heading, the semantic-chunking sentence, the follow-up)
aiq = (AIQ / "04-rag-and-retrieval" / "questions.md").read_text(encoding="utf-8")
check("### 4. What chunking strategies do you know, and how do you pick one?" in aiq, "AIQ 04 Q4 heading")
check("in practice gains are marginal over recursive+structure-aware and it adds embedding cost at ingest" in aiq, "AIQ 04 Q4 semantic-chunking sentence")
check("How do you A/B test two chunking strategies?" in aiq, "AIQ 04 Q4 follow-up")
check('"Handbook > Benefits > Parental leave"' in aiq, "AIQ 04 Q4 heading-path example")
check("MIT" in (AIQ / "LICENSE").read_text(encoding="utf-8") if (AIQ / "LICENSE").exists() else False, "AIQ LICENSE is MIT")

print(f"\n{n - fails}/{n} PASS" + ("" if fails else " — ALL PASS"))
sys.exit(1 if fails else 0)
