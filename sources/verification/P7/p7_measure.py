"""P7 (grounded prompting) measurements: every number in concepts/P7_grounded_prompting.md comes from this run.

Local only: no Groq or Cohere call, no .env read. tiktoken may download an encoding file once.
This file is also the REFERENCE SOLUTION for labs/P7_grounded_prompt_lab.ipynb (section S10 prints the
fingerprints that the lab's CHECK cells compare). Do not show it to the learner before an attempt plus a hint.

Run from rag_learning/ (Git Bash):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P7/p7_measure.py \
        "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" "<Book RAG>/upstream/RAG_Techniques"
Saved output: sources/verification/P7/out_p7_measure.txt (sections S1..S10 for P7_FACTS.md)
"""
import hashlib
import importlib.metadata as md
import json
import os
import re
import statistics as st
import sys

import pymupdf as fitz                                 # pinned 1.26.7
import tiktoken

PDF, REPO = sys.argv[1], sys.argv[2]
ENC = tiktoken.get_encoding("o200k_harmony")           # tiktoken's encoding for gpt-oss-20b (P1 S2)


def n_tok(text):
    return len(ENC.encode(text, disallowed_special=()))


def head(title):
    print(f"\n=== {title}")


def _fp(x):                                            # identical to the lab's fingerprint
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


# ================================================================ reference functions (lab solutions)
SYSTEM_V0 = (  # 06 §3.3 prompts/answer_v1.txt, SYSTEM part, verbatim (same constant as P1 p1_measure.py S9)
    "You answer questions using ONLY the numbered sources below.\n"
    "Rules:\n"
    "1. Every factual sentence must end with one or more citations in the form [doc_id:page],\n"
    "   copied exactly from the source headers, e.g. [climate:10].\n"
    "2. If the sources do not contain the answer, reply exactly:\n"
    "   \"I cannot answer this from the provided documents.\"\n"
    "   Do not use outside knowledge.\n"
    "3. Do not cite a source that does not support the sentence.\n"
    "4. Be concise: at most 5 sentences.\n")
ABSTAIN = "I cannot answer this from the provided documents."


def build_prompt(question, chunks):
    """v0 template (06 §3.3). chunks: list of dicts with doc_id, page, text, already in the order to show."""
    blocks = "\n\n".join(f"[{i}] ({c['doc_id']}:{c['page']})\n{c['text']}" for i, c in enumerate(chunks, 1))
    return SYSTEM_V0, f"Sources:\n{blocks}\n\nQuestion: {question}\nAnswer:"


def input_budget(window, max_tokens, margin):
    """Tokens left for the input after reserving the answer (max_tokens, reasoning included) and a margin."""
    return window - max_tokens - margin


def fit_blocks(fixed_tokens, block_tokens, budget):
    """How many blocks, taken in the given order, fit with the fixed part inside the budget."""
    used, k = fixed_tokens, 0
    for t in block_tokens:
        if used + t > budget:
            break
        used, k = used + t, k + 1
    return k


def edges_first(ranked):
    """Best evidence at the two edges, weakest in the middle: ranks 1,3,5,... then ...,6,4,2."""
    return ranked[0::2] + ranked[1::2][::-1]


CITE = re.compile(r"\[([A-Za-z0-9_\-]+):(\d+)\]")


def extract_citations(answer):
    return [(d, int(p)) for d, p in CITE.findall(answer)]


def invalid_citations(answer, chunks):
    allowed = {(c["doc_id"], c["page"]) for c in chunks}
    return [c for c in extract_citations(answer) if c not in allowed]


def _norm(s):
    return re.sub(r"\s+", " ", s.strip().strip('"\'').strip().rstrip(".").lower())


def is_abstention(answer):
    return _norm(answer) == _norm(ABSTAIN)


# ================================================================ S1 environment and extraction
head("S1 environment and extraction")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("pymupdf", "tiktoken")})
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
pages = [p.get_text() for p in fitz.open(PDF)]           # same extraction as the acceptance suite and P1
full = "\n".join(pages)
print(f"pages={len(pages)} chars={len(full)} encoding={ENC.name} n_vocab={ENC.n_vocab}")
print("tiktoken.encoding_for_model('gpt-oss-20b') ->", tiktoken.encoding_for_model("gpt-oss-20b").name)

# ================================================================ S2 reproduce P1 S9 (consistency)
head("S2 reproduce P1 S9: the v0 prompt over the first four 1000/200 document windows")
S, O = 1000, 200
win = [(a, min(a + S, len(full))) for a in range(0, len(full), S - O)]
starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]
page_of = lambda off: max(i + 1 for i, s0 in enumerate(starts) if s0 <= off)
Q1 = ("According to the document, by how much have global temperatures risen "
      "since the late 19th century?")                      # 06 seed D-001
p1_chunks = [{"doc_id": "climate", "page": page_of(a), "text": full[a:b]} for a, b in win[:4]]
sysm, user = build_prompt(Q1, p1_chunks)
ctx = user[len("Sources:\n"):user.index("\n\nQuestion: ")]
print(f"system={n_tok(sysm)} question={n_tok(Q1)} sources={n_tok(ctx)} user={n_tok(user)} "
      f"system+user={n_tok(sysm) + n_tok(user)}  (P1 S9 reported 107 / 20 / 842 / 869 / 976)")
p1_8 = [{"doc_id": "climate", "page": page_of(a), "text": full[a:b]} for a, b in win[:8]]
s8, u8 = build_prompt(Q1, p1_8)
print(f"same prompt with the first EIGHT windows: system+user={n_tok(s8) + n_tok(u8)} "
      f"(P1 S10 estimated ~1818 by adding 842 again)")

# ================================================================ S3 anatomy of that 976-token prompt
head("S3 anatomy of the 976-token v0 prompt (o200k_harmony)")
hdrs = [f"[{i}] ({c['doc_id']}:{c['page']})" for i, c in enumerate(p1_chunks, 1)]
texts = [c["text"] for c in p1_chunks]
parts = {
    "system rules": n_tok(sysm),
    "4 block headers": sum(n_tok(h) for h in hdrs),
    "4 chunk texts": sum(n_tok(t) for t in texts),
    "question": n_tok(Q1),
}
for k, v in parts.items():
    print(f"  {k:40s} {v:4d}")
total = n_tok(sysm) + n_tok(user)
scaff = total - sum(parts.values())
print(f"  {'scaffolding + boundary effects (rest)':40s} {scaff:4d}")
print(f"  {'total system+user':40s} {total:4d}")
print(f"header tokens each: {[n_tok(h) for h in hdrs]}")
print(f"shares: rules {parts['system rules'] / total:.1%}, chunk texts {parts['4 chunk texts'] / total:.1%},"
      f" headers {parts['4 block headers'] / total:.1%},"
      f" question {parts['question'] / total:.1%}")

# ================================================================ S4 the lab's toy ranked list (hand-picked, NOT a retrieval result)
head("S4 lab chunks: four hand-picked 1,000-char page slices for D-001 (toy ranked list, not retrieval)")
SPEC4 = [(3, 800, 1800), (10, 0, 1000), (23, 1200, 2200), (1, 1000, 2000)]
SPEC_EXTRA = [(6, 1389, 2389), (24, 0, 1000), (2, 0, 1000), (8, 0, 1000)]
mk = lambda spec: [{"doc_id": "climate", "page": p, "text": pages[p - 1][a:b]} for p, a, b in spec]
CH4, CH8 = mk(SPEC4), mk(SPEC4 + SPEC_EXTRA)
gold = "Global temperatures have risen by about 1.2 degrees Celsius (2.2 degrees Fahrenheit) since \nthe late 19th century."
print("all slices 1000 chars:", all(len(c["text"]) == 1000 for c in CH8))
print("D-001 gold sentence inside chunk 1 (p.3 [800,1800)):", gold in CH4[0]["text"])
print("numeric distractors: p.10 has '2 degrees':", "2 degrees" in CH4[1]["text"],
      "| p.23 slice has '1.5':", "1.5" in CH4[2]["text"], "| p.23 slice has '2 degrees':", "2 degrees" in CH4[2]["text"])
print("D-009 bait: p.1 slice mentions IPCC:", "IPCC" in CH4[3]["text"],
      "| any 4-digit year in the p.1 slice right after 'IPCC':",
      bool(re.search(r"IPCC\)?[^.]{0,80}\b(19|20)\d\d", CH4[3]["text"])))
s4, u4 = build_prompt(Q1, CH4)
s8b, u8b = build_prompt(Q1, CH8)
t4, t8 = n_tok(s4) + n_tok(u4), n_tok(s8b) + n_tok(u8b)
blk4 = [n_tok(f"[{i}] (climate:{c['page']})\n{c['text']}") for i, c in enumerate(CH4, 1)]
print(f"k=4 prompt: system+user={t4} tokens (chars={len(s4) + len(u4)}); block tokens incl. header={blk4}")
print(f"k=8 prompt: system+user={t8} tokens; ratio k8/k4 = {t8 / t4:.2f}")
# chunk size doubled: extend each slice to 2,000 chars inside its page
spec2k = []
for p, a, b in SPEC4:
    L = len(pages[p - 1]); a2 = max(0, min(a - 500, L - 2000)); spec2k.append((p, a2, a2 + 2000))
CH4_2k = mk(spec2k)
s2k, u2k = build_prompt(Q1, CH4_2k)
t2k = n_tok(s2k) + n_tok(u2k)
print(f"chunk size doubled to 2,000 chars ({spec2k}): system+user={t2k} tokens; ratio vs k=4/1000 = {t2k / t4:.2f}")
print("gold still inside the 2,000-char p.3 slice:", gold in CH4_2k[0]["text"])

# ================================================================ S5 block-token distribution, per-page fixed windows
head("S5 block tokens (header + text) over all per-page fixed windows (scope per page; plain slices, not the recursive splitter)")
DIST = {}
for S_, O_ in ((1000, 200), (2000, 400)):
    blocks = []
    for pno, t in enumerate(pages, 1):
        for a in range(0, len(t), S_ - O_):
            seg = t[a:a + S_]
            blocks.append((len(seg), n_tok(f"[1] (climate:{pno})\n{seg}")))
            if a + S_ >= len(t):
                break
    toks = sorted(b for _, b in blocks)
    lens = [l for l, _ in blocks]
    DIST[S_] = (toks[-1], int(st.median(toks)))
    print(f"size={S_} overlap={O_}: blocks={len(blocks)} chars mean={st.mean(lens):.0f} | tokens min={toks[0]} "
          f"median={st.median(toks)} mean={st.mean(toks):.1f} max={toks[-1]}")

# ================================================================ S6 budget arithmetic with an answer reserve (TOY windows)
head("S6 budget with answer reserve (W values are TOY, not gpt-oss-20b's real window)")
fixed = n_tok(SYSTEM_V0) + n_tok(f"Sources:\n\n\nQuestion: {Q1}\nAnswer:")
print(f"fixed part (system rules + user scaffolding + D-001 question) = {fixed} tokens")
worst, med = DIST[1000]
for W in (4096, 8192):
    B = input_budget(W, 512, 128)
    print(f"W={W}: input budget = {W} - 512 - 128 = {B}; 1000-char blocks that fit: worst-case {worst} tok -> "
          f"{fit_blocks(fixed, [worst] * 100, B)}, median {med} tok -> {fit_blocks(fixed, [med] * 100, B)}")
print("no reserve (W=4096, max_tokens=0, margin=0): worst-case blocks that fit ->",
      fit_blocks(fixed, [worst] * 100, input_budget(4096, 0, 0)))

# ================================================================ S7 repo prompt instructions: tokens and a feature audit
head("S7 repo prompts: instruction tokens and features (texts asserted against the pinned repo cells)")
cell = lambda nb, i: "".join(json.load(open(os.path.join(REPO, nb), encoding="utf-8"))["cells"][i]["source"])
CSV = ("You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer "
       "the question. If you don't know the answer, say that you don't know. Use three sentences maximum and keep the "
       "answer concise.")
LOCAL = ("You are a helpful assistant. Answer the question using ONLY the context provided below.\n"
         "If the answer is not contained in the context, respond with:\n"
         "\"I don't have enough information in the provided context to answer this question.\"\n"
         "Do not use any prior knowledge or make assumptions.")
HELPER = "For the question below, provide a concise but suffice answer based ONLY on the provided context:"
PERMISSIVE = ("You are an assistant for question-answering tasks. Answer the question based upon your knowledge. \n"
              "Use three-to-five sentences maximum and keep the answer concise.")
csv_src = cell("all_rag_techniques/simple_csv_rag.ipynb", 16)
assert all(f in csv_src for f in ['"You are an assistant for question-answering tasks. "', '"answer concise."', '"{context}"'])
assert LOCAL in cell("all_rag_techniques/local_rag_huggingface_faiss.ipynb", 22)
assert HELPER in open(os.path.join(REPO, "helper_functions.py"), encoding="utf-8").read()
assert PERMISSIVE in cell("all_rag_techniques/reliable_rag.ipynb", 18)
assert PERMISSIVE in cell("all_rag_techniques/multi_model_rag_with_captioning.ipynb", 20)
assert "docs[0].page_content" in cell("all_rag_techniques/multi_model_rag_with_captioning.ipynb", 20)
# How each pipeline labels its context blocks, as shown in the cited cells (None = no label visible in the cells)
FMT = {"simple_csv_rag 16": None,
       "local_rag_hf_faiss 22+24": "[Page {doc.metadata.get('page', '?')}]\\n{doc.page_content}",
       "helper_functions L162-205": None,
       "reliable_rag 18": "<doc{i+1}>:\\nTitle:{doc.metadata['title']}\\nSource:{doc.metadata['source']}\\nContent:...",
       "captioning 20": None,
       "v0 (06 §3.3)": "[{i}] ({doc_id}:{page})\\n{text}"}
assert "f\"[Page {doc.metadata.get('page', '?')}]\\n{doc.page_content}\"" in cell(
    "all_rag_techniques/local_rag_huggingface_faiss.ipynb", 24)
assert "<doc{i+1}>:\\nTitle:{doc.metadata['title']}\\nSource:{doc.metadata['source']}" in cell(
    "all_rag_techniques/reliable_rag.ipynb", 18)
TXT = {"simple_csv_rag 16": CSV, "local_rag_hf_faiss 22+24": LOCAL, "helper_functions L162-205": HELPER,
       "reliable_rag 18": PERMISSIVE, "captioning 20": PERMISSIVE, "v0 (06 §3.3)": SYSTEM_V0}


def audit(text, fmt):
    return {"context_only": bool(re.search(r"\bONLY\b", text)) and "your knowledge" not in text,
            "refusal": bool(re.search(r"don't know|not contained|do not contain|cannot answer", text)),
            "cite_ids": bool(re.search(r"citation|\bcite\b", text)),
            "labelled_blocks": fmt is not None,
            "invites_memory": "your knowledge" in text}


EXPECTED = {  # my reading of the cells, written before running; the run must agree
    "simple_csv_rag 16": (False, True, False, False, False),
    "local_rag_hf_faiss 22+24": (True, True, False, True, False),
    "helper_functions L162-205": (True, False, False, False, False),
    "reliable_rag 18": (False, False, False, True, True),
    "captioning 20": (False, False, False, False, True),
    "v0 (06 §3.3)": (True, True, True, True, False)}
print(f"{'prompt':28s} {'instr.tok':>9s}  context_only refusal cite_ids labelled_blocks invites_memory")
for name, text in TXT.items():
    a = audit(text, FMT[name])
    assert tuple(a.values()) == EXPECTED[name], (name, a)
    print(f"{name:28s} {n_tok(text):9d}  " + "  ".join(f"{str(v):>5s}" for v in a.values()))
print("audit agrees with the manual reading: True")

# ================================================================ S8 edges-first ordering (TOY; an algorithm, not a model measurement)
head("S8 edges-first ordering of ranked chunks (toy)")
for k in (4, 5, 8):
    r = list(range(1, k + 1))
    o = edges_first(r)
    print(f"k={k}: ranks in prompt order = {o}; middle position(s) hold rank(s) "
          f"{o[(k - 1) // 2:k // 2 + 1]}")

# ================================================================ S9 citation and abstention checks (TOY answers)
head("S9 citation and abstention checks on toy answers (written for P7, not model outputs)")
TOY = {
    "A": "Global temperatures have risen by about 1.2 degrees Celsius since the late 19th century [climate:3].",
    "B": "Temperatures rose about 1.2 degrees Celsius [climate:3]; the Paris goal is well below 2 degrees [climate:12].",
    "C": "I cannot answer this from the provided documents.",
    "D": '  "i cannot answer this from the provided documents"  ',
    "E": "I can't answer that from these sources.",
    "F": "Temperatures have risen by about 1.2 degrees Celsius.",
}
for k, a in TOY.items():
    print(f"{k}: cites={extract_citations(a)} invalid={invalid_citations(a, CH4)} abstain={is_abstention(a)}")

# ================================================================ S10 lab fingerprints
head("S10 lab CHECK fingerprints (from the reference functions above)")
STAGES = {"set chunk_size and overlap": "index", "embed every chunk": "index",
          "caption the images (captioning notebook cell 12)": "index", "embed the question": "query",
          "choose k": "query", "order the retrieved chunks": "query",
          "number the context blocks with (doc:page) headers": "query",
          "insert the answer-only-from-sources rule": "query"}
print("Task1 stages", _fp(STAGES))
print("Task2 prompt", _fp([s4, u4]), "| tokens", t4, _fp(t4))
print("Task3 tokens k8", t8, _fp(t8), "| 2000-char", t2k, _fp(t2k))
print("Task4 edges_first(1..8)", _fp(edges_first(list(range(1, 9)))))
AUD = {n: dict(zip(("context_only", "refusal", "cite_ids", "labelled_blocks", "invites_memory"), v))
       for n, v in EXPECTED.items() if n != "v0 (06 §3.3)"}
print("Task6 audit", _fp(AUD))
print("DONE")
