"""I6 study-kit measurements (K1-K12): every number the I6 lesson (document augmentation / HyPE) relies on.

The running example is v0's 97 chunks of the climate PDF (the 07 recursive chunker, per page, 1000/200, exactly as
P4's p4_kit_measure.py builds them) and the 06 section 6.7 draft seeds. The index-time questions come from the
STAND-IN question pack study/tools/examples/climate_i6_questions.jsonl: 10 questions per chunk, written on 2026-10-18
by Claude helpers that applied study/tools/examples/i6_questions_prompt_v1.txt to one chunk at a time and never saw
the eval set. It is not the Groq / Haiku replay pack the LLMOps notebook will record (study/llmops/ does not exist yet),
so every number that depends on the questions is a measurement ON THIS PACK, not on the planned generator.

Local only: no Groq, Cohere or Claude call, no .env read. MiniLM (all-MiniLM-L6-v2) loads from the local Hugging Face
cache (offline). Labels: the draft seeds are LLM-drafted and not human-verified, and 8 answerable items prove nothing:
every rank below is an observation on draft seeds, never an evaluation result.

Run from rag_learning/:
    uv run python sources/verification/I6/i6_kit_measure.py "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
Saved output: sources/verification/I6/out_i6_kit_measure.txt  (sections K1..K12 for I6_FACTS.md)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7
import tiktoken

PDF = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
EX = WS / "study" / "tools" / "examples"
PACK = EX / "climate_i6_questions.jsonl"
PROMPT = EX / "i6_questions_prompt_v1.txt"
PRICES = EX / "prices_2026-10-17.json"
L6 = "sentence-transformers/all-MiniLM-L6-v2"
NS = (1, 3, 5, 10)                                    # n served from the one n_max = 10 pack by prefix
K = 4                                                 # the course's k
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)


def head(t):
    print(f"\n=== {t}")


def f4(x):
    return f"{x:.4f}"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def snapshot(repo_id):
    ref = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{repo_id.replace('/', '--')}" / "refs" / "main"
    return ref.read_text().strip() if ref.exists() else "?"


# ---------------------------------------------------------------- the 97 chunks and the draft seeds (as P4 K1)
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                          # noqa: E402

pdf_bytes = PDF.read_bytes()
pages = [p.get_text() for p in pymupdf.open(PDF)]
md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
manifest06 = cc.build_manifest("climate", pages, pdf_bytes, {**cc.PARSER, "version": pymupdf.VersionBind}, cc.CLEANING_NONE)
SNAP = manifest06["snapshot_id"]
starts = [r["doc_char_start"] for r in manifest06["docs"][0]["page_table"]]
_core, chunking, _ = cc.load_07_modules(md07)
dch = chunking.chunk_document("climate", SNAP, pages,
                              chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page"))
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
PH = hashlib.sha256(json.dumps(CHUNKING, sort_keys=True).encode("utf-8")).hexdigest()[:12]
chunks = [{"doc_id": "climate", "snapshot_id": SNAP, "chunk_id": f"climate:{SNAP}:{PH}:{c.seq:05d}", "seq": c.seq,
           "char_start": c.char_start, "char_end": c.char_end,
           "page_segments": [{"page": g.page, "char_start": g.char_start, "char_end": g.char_end} for g in c.page_segments],
           "text": c.text, "text_sha256": c.text_sha256, "chunker": CHUNKING["name"], "params_hash": PH, "meta": {}}
          for c in dch]
SHA_JL = sha("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8"))
TEXT = [c["text"] for c in chunks]
PAGE = [c["page_segments"][0]["page"] for c in chunks]
SPAN = [("climate", c["char_start"], c["char_end"]) for c in chunks]
N = len(chunks)
TEXTS = {"climate": "\n".join(pages)}
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines()
         if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if cc.rel(SPAN[i], s["G"], TEXTS)] for s in ANS}
# the one paraphrase variant 06 section 6.7 gives (not counted among the 10 seeds; same gold as D-002)
VARIANT = {"qid": "D-002-P1", "question": "When did countries adopt the Paris climate accord?", "paraphrase_of": "D-002"}

pack = [json.loads(line) for line in PACK.read_text(encoding="utf-8").splitlines() if line.strip()]
assert [p["seq"] for p in pack] == list(range(N)), "pack must hold one line per chunk, in seq order"
assert all(p["text_sha256"] == chunks[i]["text_sha256"] for i, p in enumerate(pack)), "pack is keyed by chunk text"
QS = [p["questions"] for p in pack]


def first_rel(parents, qid):
    return next((r for r, i in enumerate(parents, 1) if i in REL[qid]), None)


def summary(ranks, k=K):
    hit1 = sum(r is not None and r <= 1 for r in ranks)
    hitk = sum(r is not None and r <= k for r in ranks)
    mrr = sum(1 / r for r in ranks if r is not None and r <= 10) / len(ranks)
    return hit1, hitk, round(mrr, 3)


def ce_at(parents, qid, k):
    return cc.ce(BYQ[qid]["G"], [SPAN[i] for i in parents[:k]], TEXTS)


# ---------------------------------------------------------------- K1
head("K1 environment, corpus, model, question pack")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "sentence-transformers", "transformers", "torch", "numpy", "tiktoken")})
print("pdf sha256", sha(pdf_bytes))
print(f"97 chunks: count={N} chunks.jsonl sha256={SHA_JL} (P4 K1: d4108b89...)")
print(f"draft seeds: {len(SEEDS)} ({len(ANS)} answerable); relevant chunk seqs per answerable seed: {REL}")
print(f"seed categories: {dict((s['qid'], s['category']) for s in SEEDS)}")
print(f"seed created_by: {sorted(Counter(s['created_by'] for s in SEEDS).items())}")
nq = sum(len(q) for q in QS)
print(f"question pack: {PACK.name} sha256={sha(PACK.read_bytes())} lines={len(pack)} questions={nq} "
      f"per chunk min={min(map(len, QS))} max={max(map(len, QS))}")
print(f"prompt: {PROMPT.name} sha256={sha(PROMPT.read_bytes())}; pack prompt_version={sorted({p['prompt_version'] for p in pack})}; "
      f"generator={sorted({p['generator'] for p in pack})}")

from sentence_transformers import SentenceTransformer  # noqa: E402

m6 = SentenceTransformer(L6, device="cpu")
print(f"{L6}: snapshot={snapshot(L6)[:8]} max_seq_length={m6.max_seq_length} dim={m6.get_embedding_dimension()}")


def enc(texts):
    return m6.encode(list(texts), convert_to_numpy=True, batch_size=32, show_progress_bar=False)


EC = enc(TEXT)                                                   # chunk vectors, unit length
FLATQ = [(p, j, q) for p, qs in enumerate(QS) for j, q in enumerate(qs)]
EQ = enc([q for _, _, q in FLATQ])                               # question vectors, unit length
QIDX = {(p, j): r for r, (p, j, _) in enumerate(FLATQ)}
QV = {s["qid"]: enc([s["question"]])[0] for s in SEEDS}
QV[VARIANT["qid"]] = enc([VARIANT["question"]])[0]
print(f"vectors: chunks {EC.shape}, questions {EQ.shape}; max |norm-1| = "
      f"{max(np.abs(np.linalg.norm(EC, axis=1) - 1).max(), np.abs(np.linalg.norm(EQ, axis=1) - 1).max()):.2e}")
ENC = tiktoken.get_encoding("o200k_harmony")
TOK = lambda t: len(ENC.encode(t))                               # noqa: E731

# ---------------------------------------------------------------- K2 upstream arithmetic
head("K2 the upstream document_augmentation parent on this PDF (read_pdf_to_string + split_document, cells 4, 6, 10)")
content = "".join(pages)                                         # helper_functions.read_pdf_to_string: content += page.get_text()
words = re.findall(r"\b\w+\b", content)
ws_words = content.split()


def split_document(document, chunk_size, chunk_overlap):        # cell 6, re-typed (stdlib only)
    tokens = re.findall(r"\b\w+\b", document)
    out = []
    for i in range(0, len(tokens), chunk_size - chunk_overlap):
        out.append(tokens[i:i + chunk_size])
        if i + chunk_size >= len(tokens):
            break
    return [" ".join(c) for c in out]


parents = split_document(content, 4000, 100)
print(f"characters={len(content):,} regex words (\\b\\w+\\b)={len(words):,} whitespace words={len(ws_words):,}")
print(f"4000/100 parents: {len(parents)}; words per parent {[len(p.split()) for p in parents]}; "
      f"share of the PDF's regex words {[round(len(p.split()) / len(words), 3) for p in parents]}")
frags = [split_document(p, 128, 16) for p in parents]
print(f"128/16 fragments per parent {[len(f) for f in frags]}; total {sum(map(len, frags))}")
print(f"o200k_harmony tokens per parent {[TOK(p) for p in parents]}; characters per parent {[len(p) for p in parents]}")
punct = sum(ch in ".,;:()%?!'\"-" for ch in content)
print(f"punctuation characters in the PDF text={punct:,}; in the parents={sum(ch in '.,;:()%?!' for p in parents for ch in p)}")
print(f"'1.2 degrees' in PDF text: {'1.2 degrees' in content}; in parent 0: {'1.2 degrees' in parents[0]}; "
      f"'1 2 degrees' in parent 0: {'1 2 degrees' in parents[0]}")
print(f"v0 chunk tokens (o200k_harmony) min/median/max = {min(map(TOK, TEXT))}/{int(np.median([TOK(t) for t in TEXT]))}/"
      f"{max(map(TOK, TEXT))}; mean {np.mean([TOK(t) for t in TEXT]):.1f}")

# ---------------------------------------------------------------- K3 toy multi-vector index
head("K3 toy multi-vector index: 8 scored vectors over 3 parents (made-up scores)")
TOY = [("v1", "A", "question", 0.81), ("v2", "B", "question", 0.74), ("v3", "B", "question", 0.72),
       ("v4", "B", "chunk", 0.70), ("v5", "B", "question", 0.69), ("v6", "C", "question", 0.66),
       ("v7", "C", "chunk", 0.55), ("v8", "A", "chunk", 0.50)]
agg = {}
for _, p, _, s in TOY:
    agg.setdefault(p, []).append(s)
mx = {p: max(v) for p, v in agg.items()}
sm = {p: round(sum(v), 2) for p, v in agg.items()}
mn = {p: round(sum(v) / len(v), 4) for p, v in agg.items()}
rk = lambda d: sorted(d, key=lambda p: (-d[p], p))              # noqa: E731
print("vectors per parent:", {p: len(v) for p, v in sorted(agg.items())})
print("max :", mx, "->", rk(mx))
print("sum :", sm, "->", rk(sm))
print("mean:", mn, "->", rk(mn))


def parent_order(kind):
    seen = []
    for _, p, kd, _ in sorted(TOY, key=lambda t: -t[3]):
        if kd == kind and p not in seen:
            seen.append(p)
    return seen


lc, lq = parent_order("chunk"), parent_order("question")
rrf = {p: round(1 / (60 + lc.index(p) + 1) + 1 / (60 + lq.index(p) + 1), 6) for p in agg}
print(f"RRF (k=60) over the chunk list {lc} and the question list {lq}: {rrf} -> {rk(rrf)}")
ranked = [p for _, p, _, _ in sorted(TOY, key=lambda t: -t[3])]
print("parents of the vectors in rank order:", ranked)
for kv in (3, 4, 6, 8):
    u = list(dict.fromkeys(ranked[:kv]))
    print(f"top {kv} vectors -> unique parents in rank order {u} ({len(u)})")
cut_first = list(dict.fromkeys(ranked[:3]))
dedup_first = list(dict.fromkeys(ranked))[:3]
print(f"k=3 parents: cut to 3 vectors then dedup = {cut_first}; dedup all then cut to 3 = {dedup_first}")
print("set() of the top-4 parents has", len(set(ranked[:4])), "members; its iteration order is not the rank order (string hashing is randomised per run)")


# LangChain MultiVectorRetriever._get_relevant_documents (langchain-classic 1.0.8, L91-L113), emulated on the toy:
def lc_multivector(vectors, k_child=4, id_key_ok=lambda v: True):
    sub_docs = sorted(vectors, key=lambda t: -t[3])[:k_child]    # vectorstore.similarity_search(query, k=4)
    ids = []
    for d in sub_docs:
        if id_key_ok(d) and d[1] not in ids:                    # first-seen parent ids, scores discarded
            ids.append(d[1])
    return ids


print(f"LangChain default emulation (4 child vectors, no oversampling): parents {lc_multivector(TOY)} "
      f"-> {len(lc_multivector(TOY))} parents for 'k = 4'; with search_kwargs k=8: {lc_multivector(TOY, 8)}")

# ---------------------------------------------------------------- K4 index size
head("K4 index size: vectors and float32 bytes (97 chunks)")
print(f"C3 baseline (Cohere 1,536-d, .npy): 128 + 97 x 1536 x 4 = {128 + 97 * 1536 * 4:,} bytes")
for n in NS:
    v1, v2 = N * (1 + n), N * n
    print(f"n={n:2d}: chunks+questions {v1:5,} vectors = {v1 / N:.0f}x; questions only {v2:5,} = {v2 / N:.0f}x | "
          f"bytes chunks+q at 1536-d {v1 * 1536 * 4:,}, at 384-d {v1 * 384 * 4:,} | q-only at 1536-d {v2 * 1536 * 4:,}, at 384-d {v2 * 384 * 4:,}")
print(f"third design (questions appended to the chunk text): {N} vectors at any n; 1536-d {N * 1536 * 4:,} bytes")

# ---------------------------------------------------------------- K5 the pack: cleaning rules, quality signals
head("K5 the stand-in pack: cleaning rules, echo, rare tokens, self-retrieval")
DEICTIC = re.compile(r"\b(the|this) (text|passage|author|document|chunk|article|context|section)\b|according to the", re.I)
NUMBERING = re.compile(r"^\s*(\d+[.)]|[-*•])\s*")


def norm_q(q):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", q.lower())).strip()


flat = [q for qs in QS for q in qs]
r_empty = sum(not q.strip() for q in flat)
r_noq = sum(not q.strip().endswith("?") for q in flat)
r_num = sum(bool(NUMBERING.match(q)) for q in flat)
r_deictic = [q for q in flat if DEICTIC.search(q)]
dup_in = sum(len(qs) - len({norm_q(q) for q in qs}) for qs in QS)
allnorm = Counter(norm_q(q) for q in flat)
dup_across = sum(c - 1 for c in allnorm.values() if c > 1)
print(f"rules on {len(flat)} questions: empty {r_empty}; not ending in '?' {r_noq}; numbering prefix {r_num}; "
      f"deictic/vague {len(r_deictic)}; duplicates inside a chunk {dup_in}; exact duplicates across chunks {dup_across}")
wl = [len(q.split()) for q in flat]
print(f"words per question min/median/max {min(wl)}/{int(np.median(wl))}/{max(wl)}; tokens per question median "
      f"{int(np.median([TOK(q) for q in flat]))}")
STOP = set("a an the of in on at to for and or is are was were be been by with from as that this what which who whom whose "
           "how why when where do does did can could would should will may might its it their there than then into about "
           "over under more most less least between such any each other some much many these those".split())


def content_words(t):
    return [w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in STOP and len(w) > 1]


echo = []
for p, qs in enumerate(QS):
    cw = set(content_words(TEXT[p]))
    for q in qs:
        w = content_words(q)
        echo.append(sum(x in cw for x in w) / len(w) if w else 0.0)
print(f"vocabulary echo: share of a question's content words that occur in its own chunk: mean {np.mean(echo):.3f}, "
      f"median {np.median(echo):.3f}; questions with every content word in the chunk: {sum(e == 1.0 for e in echo)} of {len(echo)}")
RARE = re.compile(r"\b(?:\d[\d.,]*\d|\d|[A-Z]{2,}[A-Za-z0-9]*)\b")
for n in (1, 3, 5, 10):
    kept = tot = 0
    for p, qs in enumerate(QS):
        rare = set(RARE.findall(TEXT[p]))
        joined = " ".join(qs[:n])
        tot += len(rare)
        kept += sum(bool(re.search(r"(?<![\w.])" + re.escape(r) + r"(?![\w])", joined)) for r in rare)
    print(f"rare-token retention n={n:2d}: {kept} of {tot} numbers/acronyms of the chunks appear in at least one of their questions = {kept / tot:.3f}")
own = np.array([float(EQ[QIDX[(p, j)]] @ EC[p]) for p, j, _ in FLATQ])
own_rank = []
for r, (p, j, _) in enumerate(FLATQ):
    s = EC @ EQ[r]
    own_rank.append(int((s > s[p]).sum()) + 1)
own_rank = np.array(own_rank)
print(f"cos(question, its own chunk): min {own.min():.4f} p10 {np.percentile(own, 10):.4f} median {np.median(own):.4f} max {own.max():.4f}")
print(f"own chunk's rank among 97 when the question is the query: rank 1 {int((own_rank == 1).sum())}, <=4 {int((own_rank <= 4).sum())}, "
      f"<=10 {int((own_rank <= 10).sum())}, >10 {int((own_rank > 10).sum())} (of {len(own_rank)})")
edges = [round(x * 0.1, 1) for x in range(0, 10)]
hist = [int(((own >= a) & (own < a + 0.1)).sum()) for a in edges]
print(f"histogram of cos(question, own chunk), bins of 0.1 from 0.0 to 1.0: {hist}")
cut30 = float(np.percentile(own, 30))
print(f"Doc2Query-- style filter (bi-encoder stand-in for the cross-encoder): drop the bottom 30% by cos(question, own chunk): "
      f"cut {cut30:.4f}, drops {int((own < cut30).sum())}, keeps {int((own >= cut30).sum())}")
worst = sorted(range(len(FLATQ)), key=lambda r: own[r])[:3]
print("three lowest-scoring questions (seq, cos, own rank):", [(FLATQ[r][0], f4(own[r]), int(own_rank[r])) for r in worst])
print(f"chunk 21 (page {PAGE[21]}; D-006's gold) first 3 questions: {QS[21][:3]}")
print(f"chunk 21 echo per question (n=10): {[round(echo[QIDX[(21, j)]], 2) for j in range(10)]}")
# the shape hypothesis on the pack: is a question closer to its sibling questions than to its own chunk?
closer = 0
for p, qs in enumerate(QS):
    for j in range(len(qs)):
        g = EQ[QIDX[(p, j)]]
        sib = max(float(g @ EQ[QIDX[(p, jj)]]) for jj in range(len(qs)) if jj != j)
        closer += sib > float(g @ EC[p])
print(f"questions closer to a sibling question of the same chunk than to the chunk itself: {closer} of {len(FLATQ)} = {closer / len(FLATQ):.3f}")


# ---------------------------------------------------------------- K6 retrieval on the 8 answerable seeds
def mv_scores(qv, n, design):
    """one score per stored vector; returns (scores, owner, kind, qtext) for the arm's vectors."""
    own_, kind, qtext, mats = [], [], [], []
    if design in ("chunks", "chunks+q"):
        mats.append(EC)
        own_ += list(range(N)); kind += ["chunk"] * N; qtext += [None] * N
    if design in ("chunks+q", "q-only"):
        rows = [QIDX[(p, j)] for p in range(N) for j in range(min(n, len(QS[p])))]
        mats.append(EQ[rows])
        own_ += [FLATQ[r][0] for r in rows]; kind += ["question"] * len(rows); qtext += [FLATQ[r][2] for r in rows]
    M = np.vstack(mats)
    return M @ qv, np.array(own_), kind, qtext


def parents_ranked(qv, n, design, agg="max"):
    s, ow, _, _ = mv_scores(qv, n, design)
    if agg == "max":
        best = {}
        for i in sorted(range(len(s)), key=lambda i: (-s[i], i)):
            best.setdefault(int(ow[i]), float(s[i]))
        return sorted(best, key=lambda p: (-best[p], p)), best
    tot = Counter()
    for i in range(len(s)):
        tot[int(ow[i])] += float(s[i])
    return sorted(tot, key=lambda p: (-tot[p], p)), dict(tot)


def unique_in_topk(qv, n, design, kvec):
    s, ow, _, _ = mv_scores(qv, n, design)
    top = sorted(range(len(s)), key=lambda i: (-s[i], i))[:kvec]
    return len(dict.fromkeys(int(ow[i]) for i in top))


head("K6 retrieval on the 8 answerable draft seeds (MiniLM; max per parent; dedup before the cut)")
ARMS = [("A0 chunks only (v0)", 0, "chunks")] + [(f"A1 chunks+questions n={n}", n, "chunks+q") for n in NS] + \
       [(f"A2 questions only n={n}", n, "q-only") for n in NS]
RES = {}
for name, n, design in ARMS:
    ranks, ce1, ce2, ce4 = [], 0, 0, 0
    for s in ANS:
        par, _ = parents_ranked(QV[s["qid"]], n, design)
        ranks.append(first_rel(par, s["qid"]))
        ce1 += ce_at(par, s["qid"], 1); ce2 += ce_at(par, s["qid"], 2); ce4 += ce_at(par, s["qid"], 4)
    RES[name] = ranks
    h1, h4, mrr = summary(ranks)
    print(f"{name:28s} ranks D-001..D-008={ranks} Hit@1={h1} Hit@4={h4} MRR@10={mrr:.3f} CE@1={ce1} CE@2={ce2} CE@4={ce4} (of 8)")
for name, n, design in (("A1 chunks+questions n=5, SUM", 5, "chunks+q"), ("A2 questions only n=5, SUM", 5, "q-only")):
    ranks = [first_rel(parents_ranked(QV[s["qid"]], n, design, "sum")[0], s["qid"]) for s in ANS]
    h1, h4, mrr = summary(ranks)
    print(f"{name:28s} ranks D-001..D-008={ranks} Hit@1={h1} Hit@4={h4} MRR@10={mrr:.3f}")
print(f"variant {VARIANT['qid']} {VARIANT['question']!r}: rank of chunk 27 A0="
      f"{1 + parents_ranked(QV['D-002-P1'], 0, 'chunks')[0].index(27)} A1 n=5="
      f"{1 + parents_ranked(QV['D-002-P1'], 5, 'chunks+q')[0].index(27)} A2 n=5={1 + parents_ranked(QV['D-002-P1'], 5, 'q-only')[0].index(27)}")
for n in (1, 3, 5, 10):
    for design in ("chunks+q", "q-only"):
        u = [unique_in_topk(QV[s["qid"]], n, design, K) for s in ANS]
        uo = [unique_in_topk(QV[s["qid"]], n, design, K * (n + 1)) for s in ANS]
        print(f"unique parents among the top 4 vectors, {design:8s} n={n:2d}: per seed {u} mean {np.mean(u):.2f} min {min(u)} | "
              f"top K_vec={K * (n + 1)}: min {min(uo)}")
fetch = []
for s in ANS:
    sc, ow, _, _ = mv_scores(QV[s["qid"]], 10, "chunks+q")
    order_ = sorted(range(len(sc)), key=lambda i: (-sc[i], i))
    seen, need = [], None
    for r, i in enumerate(order_, 1):
        if int(ow[i]) not in seen:
            seen.append(int(ow[i]))
        if len(seen) == K:
            need = r
            break
    fetch.append(need)
print(f"vectors fetched before 4 unique parents appear (chunks+q, n=10), per seed: {fetch}; max {max(fetch)}; bound k(n+1) = {K * 11}")

# ---------------------------------------------------------------- K7 D-006 trace
head("K7 D-006 trace: the top 12 vectors (chunks+questions, n=5) and the dedup to 4 parents")
q = QV["D-006"]
print(f"question: {BYQ['D-006']['question']!r}; gold chunk seq {REL['D-006']} (page {[PAGE[i] for i in REL['D-006']]})")
c0 = EC @ q
o0 = sorted(range(N), key=lambda i: (-c0[i], i))
print(f"A0 chunks only: top 4 {o0[:4]} pages {[PAGE[i] for i in o0[:4]]} scores {[f4(c0[i]) for i in o0[:4]]}; gold rank {o0.index(21) + 1}")
sc, ow, kd, qt = mv_scores(q, 5, "chunks+q")
order_ = sorted(range(len(sc)), key=lambda i: (-sc[i], i))
for r, i in enumerate(order_[:12], 1):
    print(f"  {r:2d} {sc[i]:.4f} {kd[i]:8s} parent {int(ow[i]):2d} (p.{PAGE[int(ow[i])]}) {qt[i] if qt[i] else ''}")
par, best = parents_ranked(q, 5, "chunks+q")
print(f"dedup in rank order -> parents {par[:4]} pages {[PAGE[i] for i in par[:4]]} scores {[f4(best[i]) for i in par[:4]]}")
print(f"unique parents in the top 12 vectors: {len(dict.fromkeys(int(ow[i]) for i in order_[:12]))}; in the top 4: "
      f"{len(dict.fromkeys(int(ow[i]) for i in order_[:4]))}")
print(f"best question score for chunk 21 vs its chunk score: {max(float(EQ[QIDX[(21, j)]] @ q) for j in range(5)):.4f} vs {c0[21]:.4f}")
for qid in ("D-001", "D-002", "D-008"):
    qq = QV[qid]
    a0 = parents_ranked(qq, 0, "chunks")[0]
    a1, b1 = parents_ranked(qq, 5, "chunks+q")
    a2 = parents_ranked(qq, 5, "q-only")[0]
    sc, ow, kd, qt = mv_scores(qq, 5, "chunks+q")
    i = max(range(len(sc)), key=lambda i: sc[i])
    print(f"{qid}: gold {REL[qid]} rank A0 {first_rel(a0, qid)} A1 {first_rel(a1, qid)} A2 {first_rel(a2, qid)}; "
          f"A1 top vector {sc[i]:.4f} {kd[i]} parent {int(ow[i])} {qt[i] or ''}")

c2 = EC @ QV["D-002"]
o2 = sorted(range(N), key=lambda i: (-c2[i], i))
print(f"D-002 chunk scores (A0): best chunk {o2[0]} {c2[o2[0]]:.4f}; gold chunk 27 {c2[27]:.4f} at rank {o2.index(27) + 1}")

# ---------------------------------------------------------------- K8 per category (the exact-term guard)
head("K8 per category: first relevant rank, A0 vs A1 n=5 vs A2 n=5")
for s in ANS:
    print(f"{s['qid']} {s['category']:20s} A0 {RES['A0 chunks only (v0)'][ANS.index(s)]} "
          f"A1 {RES['A1 chunks+questions n=5'][ANS.index(s)]} A2 {RES['A2 questions only n=5'][ANS.index(s)]}")

# ---------------------------------------------------------------- K9 leakage
head("K9 leakage: eval questions against the 970 generated questions")


def grams(t, n=3):
    w = content_words(t)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


tau_cos = float(QV["D-002"] @ QV["D-002-P1"])
print(f"the one paraphrase pair in 06 (D-002 vs D-002-P1): cos = {tau_cos:.4f}; 06 section 6.2 asks for >= 10 pairs, so tau "
      f"cannot be calibrated as a 10th percentile yet; provisional tau_cos = {tau_cos:.4f}, tau_ngram = 0.5")
LEAK = {}
for s in SEEDS + [VARIANT]:
    qq = QV[s["qid"]]
    sims = EQ @ qq
    r = int(np.argmax(sims))
    g3 = grams(s["question"])
    cont = max((len(g3 & grams(FLATQ[i][2])) / len(g3) if g3 else 0.0) for i in range(len(FLATQ)))
    LEAK[s["qid"]] = float(sims[r])
    flag = sims[r] >= tau_cos or cont >= 0.5
    print(f"{s['qid']:9s} leak_cos={sims[r]:.4f} (parent {FLATQ[r][0]}, q{FLATQ[r][1] + 1}) max_chunk_cos={float((EC @ qq).max()):.4f} "
          f"3gram_containment={cont:.3f} flagged={flag} | matched: {FLATQ[r][2]}")
flagged_g = [r for r in range(len(FLATQ)) if max(float(EQ[r] @ QV[s["qid"]]) for s in SEEDS) >= tau_cos]
print(f"generated questions with cos >= tau_cos to any of the 10 seeds: {len(flagged_g)} of {len(FLATQ)}; by parent "
      f"{sorted(Counter(FLATQ[r][0] for r in flagged_g).items())}")
keep = set(range(len(FLATQ))) - set(flagged_g)
ranks = []
for s in ANS:
    qq = QV[s["qid"]]
    best = {i: float(EC[i] @ qq) for i in range(N)}
    for r in keep:
        p, j, _ = FLATQ[r]
        if j < 5:
            best[p] = max(best[p], float(EQ[r] @ qq))
    par = sorted(best, key=lambda p: (-best[p], p))
    ranks.append(first_rel(par, s["qid"]))
h1, h4, mrr = summary(ranks)
print(f"A4 de-leaked A1 (n=5, flagged questions deleted): ranks {ranks} Hit@1={h1} Hit@4={h4} MRR@10={mrr:.3f}")

# ---------------------------------------------------------------- K10 cost and time
head("K10 index-build cost and time on the 97 chunks (one call per chunk; tokens measured with o200k_harmony)")
prices = json.loads(PRICES.read_text(encoding="utf-8"))
G, H = prices["models"]["groq:openai/gpt-oss-20b"], prices["models"]["anthropic:claude-haiku-5-5"]
tpm, tpd = prices["rate_limits"]["groq:openai/gpt-oss-20b"]["tpm"], prices["rate_limits"]["groq:openai/gpt-oss-20b"]["tpd"]
tmpl = PROMPT.read_text(encoding="utf-8")
inp = [TOK(tmpl.replace("{n_max}", "10").replace("{chunk_text}", t)) for t in TEXT]
print(f"prompt template alone {TOK(tmpl.replace('{n_max}', '10').replace('{chunk_text}', ''))} tokens; input per call min/median/max "
      f"{min(inp)}/{int(np.median(inp))}/{max(inp)}; total {sum(inp):,}")
REASON = 300                                                     # assumed reasoning tokens at low effort (UNVERIFIED)
for n in (3, 5, 10):
    out = [TOK(json.dumps({"questions": qs[:n]}, ensure_ascii=False)) for qs in QS]
    for label, extra in (("visible only", 0), (f"+{REASON} reasoning (assumed)", REASON)):
        o_tot = sum(out) + extra * N
        g = (sum(inp) * G["input"] + o_tot * G["output"]) / 1e6
        h = (sum(inp) * H["input"] + o_tot * H["output"]) / 1e6
        t_tot = sum(inp) + o_tot
        print(f"n={n:2d} {label:26s} output total {o_tot:6,} (median visible {int(np.median(out))}/call) | Groq ${g:.4f} | "
              f"Haiku ${h:.4f} (tokenizer differs: approx) | tokens {t_tot:,} -> TPM floor {t_tot / tpm:.1f} min, {t_tot / tpd:.1%} of a day")
for reb in (1, 2, 4, 30):
    print(f"HyDE break-even: rebuilt {reb:2d}x a month -> index side uses {N * reb:,} calls a month; HyDE uses one per query, "
          f"so index side has fewer calls once queries exceed {N * reb:,} a month")

# ---------------------------------------------------------------- K11 context cost
head("K11 context cost: what reaches the answer model")
ctx = []
for s in ANS:
    par, _ = parents_ranked(QV[s["qid"]], 5, "chunks+q")
    ctx.append(sum(TOK(TEXT[i]) for i in par[:4]))
print(f"k=4 parent chunks (A1 n=5) tokens per seed {ctx}; mean {np.mean(ctx):.1f}")
ctx0 = [sum(TOK(TEXT[i]) for i in parents_ranked(QV[s['qid']], 0, 'chunks')[0][:4]) for s in ANS]
print(f"k=4 chunks (A0) tokens per seed {ctx0}; mean {np.mean(ctx0):.1f}")
print(f"upstream k=1 parent: {[TOK(p) for p in parents]} tokens; the largest is {max(TOK(p) for p in parents) / np.mean(ctx0):.1f}x A0's mean")

# ---------------------------------------------------------------- K12 shape gap (checklist Q1)
head("K12 the shape gap on the seeds: best question score minus best chunk score (n=10)")
gap = {}
for s in SEEDS + [VARIANT]:
    qq = QV[s["qid"]]
    gap[s["qid"]] = float((EQ @ qq).max() - (EC @ qq).max())
print({k: f4(v) for k, v in gap.items()})
print(f"mean over the 8 answerable seeds {np.mean([gap[s['qid']] for s in ANS]):.4f}; seeds where a question beats every chunk: "
      f"{sum(gap[s['qid']] > 0 for s in ANS)} of 8; unanswerable D-009 {gap['D-009']:.4f}, D-010 {gap['D-010']:.4f}")
print(f"best score per seed, chunks vs questions: " +
      str({s['qid']: (f4(float((EC @ QV[s['qid']]).max())), f4(float((EQ @ QV[s['qid']]).max()))) for s in SEEDS}))
