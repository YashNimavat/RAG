"""C5 (context construction + generation with citations) measurements: every number in
concepts/C5_generation_citations.md comes from this run.

Local only: NO Groq or Cohere call, .env is never read. The Groq call is exercised with a FAKE client
(FakeGroq below, identical to the lab's) so the wiring can be tested without a network or a key.
Retrieval uses the LOCAL MiniLM fallback (HF cache, offline) on the v0 per-page recursive 1000/200 chunks (the same
spans and course chunk ids as the C2 lab and C4): a demo fixture for the lab, not the v0 default embedder (Cohere
embed-v4.0) and not an evaluation result. It reproduces C4's D-002 top-4.

This file is also the REFERENCE SOLUTION for labs/C5_generation_lab.ipynb (section S10 prints the
fingerprints that the lab's CHECK cells compare). Do not show it to the learner before an attempt plus a hint.

Run from rag_learning/ (Git Bash):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C5/c5_measure.py \
        "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        > sources/verification/C5/out_c5_measure.txt 2> sources/verification/C5/out_c5_measure.stderr.txt
"""
import hashlib
import importlib.metadata as md
import json
import os
import random
import re
import sys
import time
from types import SimpleNamespace

os.environ.setdefault("HF_HUB_OFFLINE", "1")           # MiniLM from the local cache only

import numpy as np                                     # noqa: E402
import pymupdf                                         # noqa: E402  pinned 1.26.7
import tiktoken                                        # noqa: E402

PDF = sys.argv[1]
ENC = tiktoken.get_encoding("o200k_harmony")           # tiktoken's encoding for gpt-oss-20b (P1 S2, P7 S1)


def n_tok(text):
    return len(ENC.encode(text, disallowed_special=()))


def head(title):
    print(f"\n=== {title}")


def _fp(x):                                            # identical to the lab's fingerprint
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ================================================================ the template file (interface assumption, 06 §3.3)
# 06 §3.3 shows the SYSTEM and USER parts with example blocks. As a FILE, the example blocks become two
# placeholders, {sources} and {question}. Everything else is 06 §3.3 verbatim (same SYSTEM text as P1/P7).
ANSWER_V1_TXT = (
    "SYSTEM:\n"
    "You answer questions using ONLY the numbered sources below.\n"
    "Rules:\n"
    "1. Every factual sentence must end with one or more citations in the form [doc_id:page],\n"
    "   copied exactly from the source headers, e.g. [climate:10].\n"
    "2. If the sources do not contain the answer, reply exactly:\n"
    "   \"I cannot answer this from the provided documents.\"\n"
    "   Do not use outside knowledge.\n"
    "3. Do not cite a source that does not support the sentence.\n"
    "4. Be concise: at most 5 sentences.\n"
    "\n"
    "USER:\n"
    "Sources:\n"
    "{sources}\n"
    "\n"
    "Question: {question}\n"
    "Answer:\n")
ABSTAIN = "I cannot answer this from the provided documents."
P7_SYSTEM_V0 = (  # copy of P7 p7_measure.py SYSTEM_V0, to prove the file gives the same system text
    "You answer questions using ONLY the numbered sources below.\n"
    "Rules:\n"
    "1. Every factual sentence must end with one or more citations in the form [doc_id:page],\n"
    "   copied exactly from the source headers, e.g. [climate:10].\n"
    "2. If the sources do not contain the answer, reply exactly:\n"
    "   \"I cannot answer this from the provided documents.\"\n"
    "   Do not use outside knowledge.\n"
    "3. Do not cite a source that does not support the sentence.\n"
    "4. Be concise: at most 5 sentences.\n")


def split_template(text):                              # GIVEN in the lab (setup cell)
    """'SYSTEM:\\n<system>\\nUSER:\\n<user pattern>' -> (system, user_pattern)."""
    head_, user = text.split("USER:\n", 1)
    assert head_.startswith("SYSTEM:\n") and head_.endswith("\n\n"), "template must start with SYSTEM: and have a blank line before USER:"
    return head_[len("SYSTEM:\n"):-1], user.rstrip("\n")


def split_sentences(text):                             # GIVEN in the lab (setup cell); a heuristic
    """A citation right after the end punctuation is moved before it; then split after . ! ? + whitespace."""
    t = re.sub(r"([.!?])((?:\s*\[[^\[\]\n]*\])+)", r"\2\1", text.strip())
    return [s for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]


class FakeGroq:                                        # GIVEN in the lab (setup cell)
    """Stands in for groq.Groq: records each call and returns a canned reply shaped like groq 1.7.0's
    ChatCompletion (choices[0].message.content, choices[0].finish_reason, usage.prompt_tokens,
    usage.completion_tokens, usage.completion_tokens_details.reasoning_tokens). No network."""

    def __init__(self, content="The Paris Agreement was adopted in 2015 [climate:10].", finish_reason="stop",
                 prompt_tokens=1000, completion_tokens=60, reasoning_tokens=40):
        self.content, self.finish_reason = content, finish_reason
        self.prompt_tokens, self.completion_tokens, self.reasoning_tokens = prompt_tokens, completion_tokens, reasoning_tokens
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        details = None if self.reasoning_tokens is None else SimpleNamespace(reasoning_tokens=self.reasoning_tokens)
        return SimpleNamespace(
            choices=[SimpleNamespace(index=0, finish_reason=self.finish_reason,
                                     message=SimpleNamespace(role="assistant", content=self.content, reasoning=None))],
            usage=SimpleNamespace(prompt_tokens=self.prompt_tokens, completion_tokens=self.completion_tokens,
                                  completion_tokens_details=details))


# ================================================================ reference functions (lab solutions)
def build_context(retrieved):
    """C4 records (rank, chunk_id, doc_id, page, score, text) -> (sources_text, chunk_ids in prompt order).
    Rank order, NOT list order. Header '[i] (doc_id:page)', blank line between blocks (P7 format)."""
    ordered = sorted(retrieved, key=lambda r: r["rank"])
    blocks = [f"[{i}] ({r['doc_id']}:{r['page']})\n{r['text']}" for i, r in enumerate(ordered, 1)]
    return "\n\n".join(blocks), [r["chunk_id"] for r in ordered]


def build_messages(question, retrieved, template_text=ANSWER_V1_TXT):
    system, user_pattern = split_template(template_text)
    sources, _ = build_context(retrieved)
    return [{"role": "system", "content": system},
            {"role": "user", "content": user_pattern.format(sources=sources, question=question)}]


def call_llm(client, messages, *, model_id, temperature=0.0, max_tokens=512, reasoning_effort="low"):
    """One chat call. Model id comes from the caller (config/.env), never hardcoded. Asserts a non-empty reply."""
    params = {"model": model_id, "temperature": temperature, "max_tokens": max_tokens, "reasoning_effort": reasoning_effort}
    t0 = time.perf_counter()
    r = client.chat.completions.create(messages=messages, **params)
    latency_ms = (time.perf_counter() - t0) * 1000
    choice = r.choices[0]
    text = choice.message.content or ""
    assert text.strip(), (f"empty answer (finish_reason={choice.finish_reason}): "
                          f"the output budget may have gone to reasoning; raise max_tokens or lower reasoning_effort")
    details = getattr(r.usage, "completion_tokens_details", None)
    return {"text": text, "finish_reason": choice.finish_reason,
            "input_tokens": r.usage.prompt_tokens, "output_tokens": r.usage.completion_tokens,
            "reasoning_tokens": getattr(details, "reasoning_tokens", None),
            "latency_ms": latency_ms, "params": params}


STRICT = re.compile(r"\[([A-Za-z0-9_\-]+):(\d+)\]")
CANDIDATE = re.compile(r"\[[^\[\]\n]*\]|\([A-Za-z0-9_\-]+\s*:\s*\d+\)")


def parse_citations(text):
    """-> (citations, malformed). citations: unique (doc_id, page) in first-appearance order, as dicts
    {marker, doc_id, page:int}. malformed: every bracket tag, or '(doc:page)' look-alike, that is not exactly
    [doc_id:page], in order of appearance."""
    cits, seen = [], set()
    for m in STRICT.finditer(text):
        key = (m.group(1), int(m.group(2)))
        if key not in seen:
            seen.add(key)
            cits.append({"marker": f"[{key[0]}:{key[1]}]", "doc_id": key[0], "page": key[1]})
    malformed = [m.group(0) for m in CANDIDATE.finditer(text) if not STRICT.fullmatch(m.group(0))]
    return cits, malformed


def check_citations(citations, retrieved):
    """Resolve each citation to the retrieved chunk ids on that doc:page (rank order). Report citations that
    resolve to nothing (cited-but-not-retrieved) and retrieved chunks no citation resolves to (not used)."""
    ordered = sorted(retrieved, key=lambda r: r["rank"])
    resolved = [{**c, "resolved_chunk_ids": [r["chunk_id"] for r in ordered
                                             if (r["doc_id"], r["page"]) == (c["doc_id"], c["page"])]}
                for c in citations]
    used = {cid for c in resolved for cid in c["resolved_chunk_ids"]}
    return {"resolved": resolved,
            "invalid": [c["marker"] for c in resolved if not c["resolved_chunk_ids"]],
            "unused_chunk_ids": [r["chunk_id"] for r in ordered if r["chunk_id"] not in used]}


def _norm(s):
    return re.sub(r"\s+", " ", s.strip().strip('"\'').strip().rstrip(".").lower())


def is_abstention(text):
    return _norm(text) == _norm(ABSTAIN)


def make_answer(text, retrieved, finish_reason="stop"):
    """finish_reason is the provider's value for this reply (make_record passes it). A hand-written toy answer
    is treated as a normal end ("stop"). 'length' = cut at the max_tokens cap; any other value, None included,
    is unexpected. Added 2026-10-09 (external-resources review §3a row 5)."""
    abstained = is_abstention(text)
    cits, malformed = parse_citations(text)
    chk = check_citations(cits, retrieved)
    uncited = 0 if abstained else sum(1 for s in split_sentences(text) if not STRICT.search(s))
    flags = set()
    if not text.strip():
        flags.add("empty")
    if chk["invalid"]:
        flags.add("cited_not_retrieved")
    if malformed:
        flags.add("malformed_tag")
    if text.strip() and not abstained and not cits:
        flags.add("no_citation")
    if cits and uncited:
        flags.add("uncited_sentence")
    if not abstained and _norm(ABSTAIN) in _norm(text):
        flags.add("abstention_inside_answer")
    if finish_reason == "length":
        flags.add("length_stop")                       # cut at the cap: can look like a citation failure (C5-A-03)
    elif finish_reason != "stop":
        flags.add("unexpected_finish_reason")          # anything else, including None (missing)
    return {"text": text, "abstained": abstained, "citations": chk["resolved"],
            "invalid_citations": chk["invalid"], "malformed_markers": malformed,
            "unused_chunk_ids": chk["unused_chunk_ids"], "uncited_sentences": uncited,
            "citation_subset_ok": not chk["invalid"] and not malformed, "flags": sorted(flags)}


def make_record(qid, question, retrieved, messages, llm_result, template_text=ANSWER_V1_TXT):
    """The C5 part of a C6 trace record (06 §2.5 field names; extra C5 fields are additive)."""
    sources, chunk_ids = build_context(retrieved)
    p = llm_result["params"]
    return {
        "qid": qid, "question": question,
        "context": {"chunk_ids": chunk_ids, "context_tokens": n_tok(sources), "tokenizer": ENC.name, "truncated_chunks": 0},
        "prompt": {"template_version": "answer_v1", "template_sha256": sha256_hex(template_text),
                   "sha256": sha256_hex(json.dumps(messages, sort_keys=True, ensure_ascii=False)),
                   "local_tokens": sum(n_tok(m["content"]) for m in messages),
                   "input_tokens": llm_result["input_tokens"]},
        "llm": {"provider": "groq", "model_id": p["model"], "temperature": p["temperature"], "max_tokens": p["max_tokens"],
                "reasoning_effort": p["reasoning_effort"], "finish_reason": llm_result["finish_reason"], "cache_hit": False},
        "answer": {**make_answer(llm_result["text"], retrieved, finish_reason=llm_result["finish_reason"]),
                   "output_tokens": llm_result["output_tokens"], "reasoning_tokens": llm_result["reasoning_tokens"]},
        "latency_ms": {"llm": llm_result["latency_ms"]},
        "errors": [],
    }


def failing_qids(records):
    """The 02 evidence check: cited IDs must be a subset of retrieved IDs (and every tag parseable).
    A record with an error (e.g. an empty answer) also fails: an empty answer is a failure, not a skip."""
    return [r["qid"] for r in records if not r["answer"]["citation_subset_ok"] or r["errors"]]


# ================================================================ S1 environment, extraction, snapshot
head("S1 environment, extraction, snapshot")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("pymupdf", "tiktoken", "numpy", "sentence-transformers", "groq")})
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
pages = [p.get_text() for p in pymupdf.open(PDF)]
doc_text = "\n".join(pages)
print(f"pages={len(pages)} chars={len(doc_text)} encoding={ENC.name}")
dts = sha256_hex(doc_text)
parts = ["snapshot-v1", "parser=pymupdf@1.26.7", "options=" + json.dumps({}, sort_keys=True), "cleaning=none", "page_join=\\n",
         f"climate:{dts}"]
SNAPSHOT_ID = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]   # 06 §5.3 recipe
print(f"doc_text_sha256={dts}  snapshot_id={SNAPSHOT_ID}  (06 §5.3 states ea07572562ac: {SNAPSHOT_ID == 'ea07572562ac'})")


# ================================================================ S2 chunks and chunk ids
head("S2 chunks: the v0 per-page recursive 1000/200 spans (07 H.1/H.3 via the acceptance suite's loader, as C2 lab and C4); ids per 06 §2.3")
from pathlib import Path  # noqa: E402

WS = Path(__file__).resolve().parents[3]                                   # rag_learning/
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                                                # noqa: E402  (read-only import)

_core, _chunking, _ = cc.load_07_modules((WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8"))
_dch = _chunking.chunk_document("climate", SNAPSHOT_ID, pages,
                                _chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page"))
# Course-wide id decision (coordinator, 2026-10-08; = C2 lab Task 7, C4): params_hash over 06 §2.4's chunking block.
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
PARAMS_HASH = hashlib.sha256(json.dumps(CHUNKING, sort_keys=True).encode("utf-8")).hexdigest()[:12]
CH = [(c.seq, c.page_segments[0].page, c.char_start, c.char_end) for c in _dch]   # DOCUMENT offsets
assert all(doc_text[a_:b_] == c.text for (_, _, a_, b_), c in zip(CH, _dch)) and all(len(c.page_segments) == 1 for c in _dch)
cid = lambda seq: f"climate:{SNAPSHOT_ID}:{PARAMS_HASH}:{seq:05d}"
_jl = "".join(json.dumps({"doc_id": "climate", "snapshot_id": SNAPSHOT_ID, "chunk_id": cid(c.seq), "seq": c.seq,
                          "char_start": c.char_start, "char_end": c.char_end,
                          "page_segments": [{"page": g.page, "char_start": g.char_start, "char_end": g.char_end} for g in c.page_segments],
                          "text": c.text, "text_sha256": c.text_sha256, "chunker": CHUNKING["name"], "params_hash": PARAMS_HASH,
                          "meta": {}}, ensure_ascii=False) + "\n" for c in _dch).encode("utf-8")
print(f"params_hash={PARAMS_HASH} (course id 1ca9c5a3b548: {PARAMS_HASH == '1ca9c5a3b548'}) chunks={len(CH)} "
      f"example chunk_id={cid(0)}")
print("chunks.jsonl sha256 equals the C2 lab / C4 file d4108b89…:",
      hashlib.sha256(_jl).hexdigest() == "d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b")

# ================================================================ S3 local retrieval (demo fixture for the lab)
head("S3 local MiniLM retrieval (fallback model, exact cosine, ties by chunk_id; = C4's v0 stand-in; DEMO FIXTURE, not evaluation)")
from sentence_transformers import SentenceTransformer  # noqa: E402

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
texts = [doc_text[a_:b_] for _, _, a_, b_ in CH]
V = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
SEEDS = {  # 06 §6.7 draft seeds (llm-draft; demo only)
    "D-001": "According to the document, by how much have global temperatures risen since the late 19th century?",
    "D-002": "In what year was the Paris Agreement adopted?",
    "D-003": "According to the document, what is essential regarding countries' nationally determined contributions (NDCs) for meeting the Paris Agreement's goals?",
    "D-004": "What does DAC stand for, and what does it do?",
    "D-005": "How does the document contrast coal and natural gas in terms of carbon intensity?",
    "D-006": "What are the advantages of putting solar panels on lakes or reservoirs?",
    "D-007": "What is the supreme decision-making body of the convention that provides the framework for negotiating the Kyoto Protocol and the Paris Agreement?",
    "D-008": "What does the Kigali Amendment target?",
    "D-009": "In what year was the IPCC established?",
    "D-010": "What share of global greenhouse gas emissions comes from aviation?",
}
GOLD_PAGES = {"D-001": [3], "D-002": [10], "D-003": [23], "D-004": [8, 23], "D-005": [2], "D-006": [8],
              "D-007": [10, 29], "D-008": [24], "D-009": [], "D-010": []}
Q = model.encode(list(SEEDS.values()), normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
S = Q @ V.T
TOP = {}
for (qid, _), s in zip(SEEDS.items(), S):
    order = sorted(range(len(CH)), key=lambda i: (-float(s[i]), cid(CH[i][0])))     # ties by chunk_id (06 §3.1)
    TOP[qid] = [(CH[i][0], CH[i][1], CH[i][2], CH[i][3], round(float(s[i]), 4)) for i in order[:8]]
    print(qid, "top-4 (seq, page, doc_start, doc_end, score):", TOP[qid][:4], "| gold pages", GOLD_PAGES[qid],
          "| a gold PAGE in top-4 (page level only):", any(p in GOLD_PAGES[qid] for _, p, _, _, _ in TOP[qid][:4]))


def records(spec):
    """C4's retrieval result as C5 consumes it (interface assumption): rank, chunk_id, doc_id, page, score, text."""
    return [{"rank": i, "chunk_id": cid(seq), "doc_id": "climate", "page": p, "score": sc, "text": doc_text[a:b]}
            for i, (seq, p, a, b, sc) in enumerate(spec, 1)]


R4, R8, R9 = records(TOP["D-002"][:4]), records(TOP["D-002"][:8]), records(TOP["D-009"][:4])
print("D-002 top-8 (rank, page, score):", [(r["rank"], r["page"], r["score"]) for r in R8])
gold002 = "The Paris Agreement, adopted in 2015, aims to limit global warming to well below 2 degrees Celsius"
print("D-002 gold quote inside which top-4 ranks:", [r["rank"] for r in R4 if gold002 in re.sub(r"\s+", " ", r["text"])])
print("D-002 top-4 chunks containing '2015':", [r["rank"] for r in R4 if "2015" in r["text"]])
print("D-009 top-4 pages:", [r["page"] for r in R9], "| same-page pairs:",
      sorted({r["page"] for r in R9 if [x["page"] for x in R9].count(r["page"]) > 1}))
print("'IPCC' on pages:", [i + 1 for i, t in enumerate(pages) if "IPCC" in t], "| '1988' anywhere:", "1988" in doc_text,
      "| p.1 in D-009 top-4:", 1 in [r["page"] for r in R9])

# ================================================================ S4 template, messages, tokens
head("S4 template file, messages, token counts (o200k_harmony)")
sysm, upat = split_template(ANSWER_V1_TXT)
print("system part == P7 SYSTEM_V0:", sysm == P7_SYSTEM_V0, "| user pattern:", repr(upat))
TEMPLATE_SHA = sha256_hex(ANSWER_V1_TXT)
print("template sha256:", TEMPLATE_SHA, "| one extra space changes it:", sha256_hex(ANSWER_V1_TXT + " ") != TEMPLATE_SHA)
# consistency with P7 S4: same chunks -> same 958 tokens
P7SPEC = [(3, 800, 1800), (10, 0, 1000), (23, 1200, 2200), (1, 1000, 2000)]
p7r = [{"rank": i, "chunk_id": f"x{i}", "doc_id": "climate", "page": p, "text": pages[p - 1][a:b]} for i, (p, a, b) in enumerate(P7SPEC, 1)]
Q1 = SEEDS["D-001"]
m_p7 = build_messages(Q1, p7r)
print("P7 lab chunks through the template file: system+user tokens =", sum(n_tok(m["content"]) for m in m_p7), "(P7 S4: 958)")
Q2 = SEEDS["D-002"]
M4 = build_messages(Q2, R4)
src4, ids4 = build_context(R4)
tok4 = sum(n_tok(m["content"]) for m in M4)
print(f"D-002 k=4: system={n_tok(M4[0]['content'])} user={n_tok(M4[1]['content'])} system+user={tok4} "
      f"context_tokens(sources)={n_tok(src4)} chars={sum(len(m['content']) for m in M4)}")
print("D-002 k=4 block tokens incl. header:", [n_tok(f"[{i}] ({r['doc_id']}:{r['page']})\n{r['text']}") for i, r in enumerate(R4, 1)])
print("D-002 headers in prompt order:", re.findall(r"^\[\d+\] \(.*\)$", M4[1]["content"], re.M))
shuf = R4[:]
random.Random(0).shuffle(shuf)
print("shuffled input order:", [r["rank"] for r in shuf], "| same messages after rank sort:", build_messages(Q2, shuf) == M4)
MSG_SHA = sha256_hex(json.dumps(M4, sort_keys=True, ensure_ascii=False))
print("messages sha256 (D-002, k=4):", MSG_SHA)
M8 = build_messages(Q2, R8)
tok8 = sum(n_tok(m["content"]) for m in M8)
print(f"D-002 k=8: system+user={tok8}; ratio k8/k4 = {tok8 / tok4:.2f}; context_tokens k8={n_tok(build_context(R8)[0])}")
M9 = build_messages(SEEDS["D-009"], R9)
print("D-009 k=4: system+user =", sum(n_tok(m["content"]) for m in M9))
all10 = {q: sum(n_tok(m["content"]) for m in build_messages(SEEDS[q], records(TOP[q][:4]))) for q in SEEDS}
print("10 seed prompts (k=4) system+user tokens:", all10, "| min", min(all10.values()), "max", max(all10.values()),
      "sum", sum(all10.values()))

# ================================================================ S5 the call, wired against a fake client
head("S5 call_llm against FakeGroq (no network)")
fk = FakeGroq()
res = call_llm(fk, M4, model_id="fake-model-x")
print("kwargs sent:", {k: v for k, v in fk.calls[0].items() if k != "messages"}, "| messages passed through:", fk.calls[0]["messages"] is M4)
print("result:", {k: v for k, v in res.items() if k != "latency_ms"})
for label, kw in [("empty string", {"content": ""}), ("None", {"content": None}), ("whitespace", {"content": "  \n"}),
                  ("empty at length cap", {"content": "", "finish_reason": "length"})]:
    try:
        call_llm(FakeGroq(**kw), M4, model_id="m")
        print(f"{label}: NO assertion (bug)")
    except AssertionError as e:
        print(f"{label}: AssertionError -> {e}")
print("usage without completion_tokens_details -> reasoning_tokens:",
      call_llm(FakeGroq(reasoning_tokens=None), M4, model_id="m")["reasoning_tokens"])
# Added 2026-10-09 (external-resources review §3a row 5): a NON-empty reply cut at the cap passes the assert,
# so the record must flag it. Hand-written toy reply, not a model output.
CUT = "The Paris Agreement was adopted in 2015 [climate:10]. It aims to limit warming to"
cut = make_record("D-002", Q2, R4, M4, call_llm(FakeGroq(content=CUT, finish_reason="length"), M4, model_id="m"))
print(f"cut-off reply {CUT!r} with finish_reason='length': call_llm passes; answer flags = {cut['answer']['flags']}; "
      f"citation_subset_ok = {cut['answer']['citation_subset_ok']}; failing_qids([record]) = {failing_qids([cut])}")
for fr in ("stop", "length", "tool_calls", None):
    print(f"make_answer(T01 text, finish_reason={fr!r}) flags:",
          make_answer("The Paris Agreement was adopted in 2015 [climate:10].", R4, finish_reason=fr)["flags"])

# ================================================================ S6 hand-written toy answers through the checks
head("S6 hand-written toy answers (NOT model outputs) through parse/check/make_answer; D-002 top-4 unless noted")
TOY = [  # (id, text, retrieved set)
    ("T01 good", "The Paris Agreement was adopted in 2015 [climate:10].", "R4"),
    ("T02 fabricated page", "The Paris Agreement was adopted in 2015 [climate:12].", "R4"),
    ("T03 wrong doc id", "The Paris Agreement was adopted in 2015 [paris:10].", "R4"),
    ("T04 case differs", "The Paris Agreement was adopted in 2015 [Climate:10].", "R4"),
    ("T05 no citation", "The Paris Agreement was adopted in 2015.", "R4"),
    ("T06 one of two uncited", "The Paris Agreement was adopted in 2015 [climate:10]. It aims to limit warming to well below 2 degrees Celsius.", "R4"),
    ("T07 block number", "The Paris Agreement was adopted in 2015 [4].", "R4"),
    ("T08 space inside", "The Paris Agreement was adopted in 2015 [climate: 10].", "R4"),
    ("T09 header copy ()", "The Paris Agreement was adopted in 2015 (climate:10).", "R4"),
    ("T10 two in one []", "The Paris Agreement was adopted in 2015 [climate:10, climate:24].", "R4"),
    ("T11 after full stop", "The Paris Agreement was adopted in 2015. [climate:10]", "R4"),
    ("T12 two valid tags", "The Paris Agreement was adopted in 2015 [climate:10][climate:24].", "R4"),
    ("T13 exact abstention", "I cannot answer this from the provided documents.", "R4"),
    ("T14 abstention variant", '  "i cannot answer this from the provided documents"  ', "R4"),
    ("T15 paraphrased refusal", "The sources do not say when the Paris Agreement was adopted.", "R4"),
    ("T16 abstention + tag", "I cannot answer this from the provided documents [climate:23].", "R4"),
    ("T17 empty", "", "R4"),
    ("T18 D-009 abstention", "I cannot answer this from the provided documents.", "R9"),
    ("T19 D-009 memory+valid tag", "The IPCC was established in 1988 [climate:29].", "R9"),
]
SETS = {"R4": R4, "R9": R9}
short = lambda c: c.split(":")[-1]
for tid, text, rs in TOY:
    a = make_answer(text, SETS[rs])
    print(f"{tid:28s} cits={[(c['marker'], [short(x) for x in c['resolved_chunk_ids']]) for c in a['citations']]} "
          f"invalid={a['invalid_citations']} malformed={a['malformed_markers']} unused={[short(x) for x in a['unused_chunk_ids']]} "
          f"uncited={a['uncited_sentences']} abstained={a['abstained']} subset_ok={a['citation_subset_ok']} flags={a['flags']}")
print("split_sentences(T11):", split_sentences(TOY[10][1]), "| split_sentences('About 1.2 degrees. Yes.'):",
      split_sentences("About 1.2 degrees. Yes."))

# ================================================================ S7 diagnosis key (CR-11), taught in Part J and lab Task 7
head("S7 diagnosis scenarios (lab Task 7): kind of failure and which v0 check catches it")
DIAG = {
    "a": ("D-002, gold p.10 retrieved (rank 3); answer T02 cites [climate:12]", "generation", "subset_check"),
    "b": ("D-002, gold p.10 retrieved; answer T01 cites only p.10; p.24, p.23, p.6 unused", "none", "nothing_to_catch"),
    "c": ("D-009 (unanswerable); answer T19 '1988 [climate:29]', p.29 was retrieved", "generation", "not_caught_in_v0"),
    "d": ("gold page not in top-4; answer is the exact abstention sentence", "retrieval", "retrieval_metric"),
    "e": ("D-002, gold p.10 retrieved; answer 'adopted in 2016 [climate:23]'", "generation", "not_caught_in_v0"),
    "f": ("gold page not in top-4; answer correct, no citation", "both", "no_citation_flag"),
}
for k, (s, kind, by) in DIAG.items():
    print(f"{k}: {kind:10s} {by:18s} | {s}")
print("e: answer check:", make_answer("The Paris Agreement was adopted in 2016 [climate:23].", R4)["flags"],
      make_answer("The Paris Agreement was adopted in 2016 [climate:23].", R4)["citation_subset_ok"])

# ================================================================ S8 CR-08 probes
head("S8 CR-08: k doubles; max_tokens halves")
a4 = make_answer(TOY[0][1], R4)
a8 = make_answer(TOY[0][1], R8)
print(f"T01 with k=4: unused {len(a4['unused_chunk_ids'])} of 4; with k=8: unused {len(a8['unused_chunk_ids'])} of 8")
print(f"prompt tokens k=4 -> k=8: {tok4} -> {tok8} (x{tok8 / tok4:.2f})")
for W in (8192,):
    for mt in (512, 256):
        print(f"TOY window {W}: input budget with max_tokens={mt}, margin 128 = {W - mt - 128}")
print("10-query run, upper bound on billed output tokens at max_tokens=512:", 10 * 512,
      "| local input tokens (sum, before provider template overhead):", sum(all10.values()))

# ================================================================ S9 the answer record (shape) for T01 via FakeGroq
head("S9 answer record (C5 output, consumed by C6's trace); FakeGroq reply = hand-written T01; latency rounded")
rec = make_record("D-002", Q2, R4, M4, call_llm(FakeGroq(), M4, model_id="openai/gpt-oss-20b"))
rec["latency_ms"]["llm"] = 0.0          # fake call: its latency is meaningless, so it is zeroed for a stable printout
print(json.dumps(rec, indent=1, ensure_ascii=False))
TOYREC = [make_record(f"T{i:02d}", "q", R4, M4,
                      {"text": t, "finish_reason": "stop", "input_tokens": None, "output_tokens": None, "reasoning_tokens": None,
                       "latency_ms": 0.0, "params": {"model": "m", "temperature": 0.0, "max_tokens": 512, "reasoning_effort": "low"}})
          for i, t in [(1, TOY[0][1]), (2, TOY[1][1]), (5, TOY[4][1]), (7, TOY[6][1]), (13, TOY[12][1]), (12, TOY[11][1])]]
TOYREC[2]["errors"].append("empty answer (finish_reason=length)")   # pretend T05's call had failed
print("failing_qids on toy records T01,T02,T05(+error),T07,T13,T12:", failing_qids(TOYREC))

# ================================================================ S10 lab fingerprints
head("S10 lab fingerprints (_fp = first 16 hex of sha256(json.dumps(x, sort_keys=True)))")
FP = {
    "task1 messages D-002 k=4": _fp(M4),
    "task1 tokens k=4": _fp(tok4),
    "task1 template sha": _fp(TEMPLATE_SHA),
    "task3 parse T10": _fp(parse_citations(TOY[9][1])),
    "task4 check D-009 T19": _fp(check_citations(parse_citations(TOY[18][1])[0], R9)),
    "task5 answers T01..T19": _fp([make_answer(t, SETS[r]) for _, t, r in TOY]),
    "task7 kinds": _fp({k: v[1] for k, v in DIAG.items()}),
    "task7 caught_by": _fp({k: v[2] for k, v in DIAG.items()}),
    "task8 tokens k=8": _fp(tok8),
    "task8 unused k=8": _fp(len(a8["unused_chunk_ids"])),
}
for k, v in FP.items():
    print(f"{k:28s} {v}")
print("lab fixture: SNAPSHOT_ID", SNAPSHOT_ID, "PARAMS_HASH", PARAMS_HASH)
print("lab fixture TOP4 (all 10 seeds):", json.dumps({q: TOP[q][:4] for q in SEEDS}))
print("lab fixture D-002 ranks 5-8:", TOP["D-002"][4:8])
