"""I6: check every repo cell, script line, framework source line and interview quote the I6 lesson cites.

Reads (never executes) the pinned files:
  <upstream>/RAG_Techniques @ 009adba2: all_rag_techniques/document_augmentation.ipynb, HyPE_Hypothetical_Prompt_Embeddings.ipynb,
      all_rag_techniques_runnable_scripts/document_augmentation.py, HyPE_Hypothetical_Prompt_Embeddings.py, helper_functions.py
  <upstream>/AI-Engineer-Interview-Questions @ e080df2: 04-rag-and-retrieval/questions.md (MIT, Copyright (c) 2026 Om)
  [optional] <libs>/multi_vector.py (langchain-classic==1.0.8), vectorstores_base.py (langchain-core==1.6.6),
      metadata_extractors.py (llama-index-core v0.14.25), as downloaded from raw.githubusercontent.com at those tags.
Cells are 0-based. Prints one PASS/FAIL line per check and ALL PASS at the end.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run python sources/verification/I6/i6_sources.py "<Book RAG>/upstream" [<libs dir>] \
        > sources/verification/I6/out_i6_sources.txt
"""
import ast
import json
import sys
from pathlib import Path

UP = Path(sys.argv[1])
LIBS = Path(sys.argv[2]) if len(sys.argv) > 2 else None
RT = UP / "RAG_Techniques"
fails = 0


def check(ok, msg):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + msg)


def cells(nb):
    d = json.loads((RT / "all_rag_techniques" / nb).read_text(encoding="utf-8"))
    return d["cells"]


def src(c):
    return "".join(c["source"])


def lines(p, a, b):
    return "\n".join(p.read_text(encoding="utf-8").splitlines()[a - 1:b])


# ---------------------------------------------------------------- document_augmentation.ipynb
da = cells("document_augmentation.ipynb")
check(len(da) == 19, f"document_augmentation.ipynb has 19 cells ({len(da)})")
check(not any(c.get("outputs") for c in da if c["cell_type"] == "code"), "document_augmentation.ipynb: no saved output in any cell")
c4 = src(da[4])
for s in ("DOCUMENT_MAX_TOKENS = 4000", "DOCUMENT_OVERLAP_TOKENS = 100", "FRAGMENT_MAX_TOKENS = 128",
          "FRAGMENT_OVERLAP_TOKENS = 16", "QUESTION_GENERATION = QuestionGeneration.DOCUMENT_LEVEL", "QUESTIONS_PER_DOCUMENT = 40"):
    check(s in c4, f"doc-aug cell 4: {s}")
c6 = src(da[6])
for s in (r"re.sub(r'^\d+\.\s*', ''", "if cleaned_question.endswith('?')", 'model="gpt-4o-mini", temperature=0',
          "at least {num_questions}", "directly answerable within the context and do not include any answers or headers",
          "with_structured_output(QuestionList)", "return list(set(filtered_questions))", r"re.findall(r'\b\w+\b', document)",
          'return [" ".join(chunk) for chunk in chunks]'):
    check(s in c6, f"doc-aug cell 6: {s}")
c10 = src(da[10])
for s in ('"text": text_document', 'search_kwargs={"k": 1}', "QuestionGeneration.FRAGMENT_LEVEL", '"type": "AUGMENTED"'):
    check(s in c10, f"doc-aug cell 10: {s}")
check("context = doc.metadata['text']" in src(da[17]) and "for doc in retrieved_documents" in src(da[15]),
      "doc-aug cells 15/17: the parent comes from the loop variable `doc` left over from cell 15")
check("read_pdf_to_string(path)" in src(da[13]), "doc-aug cell 13: read_pdf_to_string on the climate PDF")
hf = (RT / "helper_functions.py").read_text(encoding="utf-8")
check("content += page.get_text()" in hf and "def read_pdf_to_string" in hf, "helper_functions.read_pdf_to_string: PyMuPDF, pages concatenated with no separator")
dap = RT / "all_rag_techniques_runnable_scripts" / "document_augmentation.py"
p65 = lines(dap, 65, 66)
check("at least {num_questions}" in p65 and "directly answerable" not in dap.read_text(encoding="utf-8"),
      "document_augmentation.py L65-L66: prompt WITHOUT the notebook's 'directly answerable ... no answers or headers' clause")

# ---------------------------------------------------------------- HyPE notebook
hy = cells("HyPE_Hypothetical_Prompt_Embeddings.ipynb")
check(len(hy) == 23, f"HyPE notebook has 23 cells ({len(hy)})")
check("Up to 42 percentage points" in src(hy[0]) and "Up to 45 percentage points" in src(hy[0]) and "5139335" in src(hy[0]),
      "HyPE cell 0: claims 'up to' +42 pp precision and +45 pp claim recall, SSRN 5139335")
check('LANGUAGE_MODEL_NAME = "gpt-4o-mini"' in src(hy[7]) and 'EMBEDDING_MODEL_NAME = "text-embedding-3-small"' in src(hy[7])
      and "CHUNK_SIZE = 1000" in src(hy[7]) and "CHUNK_OVERLAP = 200" in src(hy[7]), "HyPE cell 7: gpt-4o-mini, text-embedding-3-small, 1000/200")
check('.replace("\\n\\n", "\\n").split("\\n")' in src(hy[9]) and "essential questions" in src(hy[9]),
      "HyPE cell 9: free-text 'essential questions', split on newlines, no question count")
try:
    ast.parse(src(hy[11]))
    syn = None
except SyntaxError as e:
    syn = e.lineno
check(syn == 32, f"HyPE cell 11: SyntaxError at cell line 32 (got {syn})")
check("(chunk.page_content, vec) for vec in vectors" in src(hy[11]) and "metadata" not in src(hy[11]).split("chunks_with_embedding_vectors =")[1],
      "HyPE cell 11: add_embeddings((page_content, vec)) with no metadata")
check("RecursiveCharacterTextSplitter" in src(hy[13]) and "PyPDFLoader" in src(hy[13]), "HyPE cell 13: PyPDFLoader + RecursiveCharacterTextSplitter")
out15 = "".join("".join(o.get("text", "")) for o in hy[15].get("outputs", []))
check("97/97" in out15 and hy[11]["execution_count"] == 66 and hy[15]["execution_count"] == 71,
      "HyPE cell 15: saved output 97/97 (exec 71) after the broken cell 11 (exec 66): outputs predate the edit")
check('search_kwargs={"k": 3}' in src(hy[17]), "HyPE cell 17: k=3")
out19 = "".join("".join(o.get("text", "")) for o in hy[19].get("outputs", []))
check("list(set(context))" in src(hy[19]) and "Context 3:" in out19 and "Context 4:" not in out19,
      "HyPE cell 19: list(set(context)); saved output shows 3 distinct contexts for k = 3 (research I6 section 1 said 2: "
      "corrected, error I6-E10); set() order is not the rank order")
hyp = RT / "all_rag_techniques_runnable_scripts" / "HyPE_Hypothetical_Prompt_Embeddings.py"
check("index=faiss.IndexFlatL2(len(vectors[0]))," in lines(hyp, 99, 99), "HyPE script L99: the missing comma is fixed")
check("context = list(set(context))" in lines(hyp, 152, 152), "HyPE script L152: dedup with set()")

# ---------------------------------------------------------------- interview repo
aiq = (UP / "AI-Engineer-Interview-Questions" / "04-rag-and-retrieval" / "questions.md").read_text(encoding="utf-8")
lic = (UP / "AI-Engineer-Interview-Questions" / "LICENSE").read_text(encoding="utf-8")
check("MIT License" in lic and "Copyright (c) 2026 Om" in lic, "AIQ LICENSE: MIT, Copyright (c) 2026 Om")
check("### 45. How do you build a golden evaluation set for RAG without months of labelling?" in aiq, "AIQ Q45 heading verbatim")
check("echo the chunk's vocabulary, inflating retrieval scores" in aiq, "AIQ Q45: synthetic questions echo the chunk's vocabulary")

# ---------------------------------------------------------------- framework sources (optional)
if LIBS:
    mv = LIBS / "multi_vector.py"
    check('id_key: str = "doc_id"' in lines(mv, 55, 55), "langchain-classic 1.0.8 multi_vector.py L55: id_key='doc_id'")
    check("search_kwargs: dict = Field(default_factory=dict)" in lines(mv, 57, 57), "L57: search_kwargs={} (no k)")
    check("search_type: SearchType = SearchType.similarity" in lines(mv, 60, 60), "L60: search_type=similarity")
    blk = lines(mv, 107, 113)
    check("if self.id_key in d.metadata and d.metadata[self.id_key] not in ids:" in blk and "self.docstore.mget(ids)" in blk
          and "if d is not None" in blk, "L107-L113: first-seen parent ids, scores dropped, children without id_key and missing parents dropped")
    vb = LIBS / "vectorstores_base.py"
    check("self, query: str, k: int = 4, **kwargs: Any" in lines(vb, 361, 362), "langchain-core 1.6.6 vectorstores/base.py L361-L362: similarity_search k=4")
    me = LIBS / "metadata_extractors.py"
    check("default=5," in lines(me, 282, 283), "llama-index-core 0.14.25 metadata_extractors.py L282-L283: questions default 5")
    check("unlikely to be found elsewhere" in lines(me, 253, 265), "L253-L265: prompt asks for questions 'unlikely to be found elsewhere'")
    check('"questions_this_excerpt_can_answer"' in lines(me, 334, 334), "L334: stored as metadata questions_this_excerpt_can_answer")
else:
    print("SKIPPED framework source lines (no libs dir given)")

print("ALL PASS" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
