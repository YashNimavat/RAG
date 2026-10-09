"""P4 (embeddings and similarity) measurements: every number in concepts/P4_embeddings_similarity.md comes from this run.

Local only: no Groq or Cohere calls, no .env read. Models load from the local Hugging Face cache (offline forced below):
  sentence-transformers/all-MiniLM-L6-v2      (bi-encoder, has a Normalize module)
  sentence-transformers/paraphrase-MiniLM-L3-v2 (bi-encoder, NO Normalize module; used as the "other model")
  cross-encoder/ms-marco-MiniLM-L-6-v2        (cross-encoder, the reranker of reranking.ipynb cell 27)

Run from rag_learning/ (Git Bash or PowerShell):
    uv run python sources/verification/P4/p4_measure.py "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
Saved output: sources/verification/P4/out_p4_measure.txt (sections S1..S10, referenced by P4_FACTS.md)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import hashlib
import heapq
import importlib.metadata as md
import re
import sys

import numpy as np
import pymupdf as fitz

PDF = sys.argv[1]
L6 = "sentence-transformers/all-MiniLM-L6-v2"
L3 = "sentence-transformers/paraphrase-MiniLM-L3-v2"
CE = "cross-encoder/ms-marco-MiniLM-L-6-v2"
np.set_printoptions(suppress=True)


def head(t):
    print(f"\n=== {t}")


def cos(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def l2(a, b):
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


def unit(a):
    a = np.asarray(a, float)
    return a / np.linalg.norm(a)


def snapshot(repo_id):
    ref = os.path.expanduser(f"~/.cache/huggingface/hub/models--{repo_id.replace('/', '--')}/refs/main")
    return open(ref).read().strip() if os.path.exists(ref) else "?"


# ------------------------------------------------------------------ S1
head("S1 environment, corpus, models")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "transformers", "sentence-transformers", "torch", "numpy", "tokenizers")})
print("pdf sha256", hashlib.sha256(open(PDF, "rb").read()).hexdigest())
pages = [p.get_text() for p in fitz.open(PDF)]
full = "\n".join(pages)                                    # acceptance-suite convention
S, O = 1000, 200                                           # plain fixed character windows, as in P1 S4
windows = [full[i:i + S] for i in range(0, len(full), S - O)]
print(f"pages={len(pages)} chars={len(full)} windows(1000/200, plain slices)={len(windows)} last_len={len(windows[-1])}")

from sentence_transformers import CrossEncoder, SentenceTransformer  # noqa: E402

m6 = SentenceTransformer(L6, device="cpu")
m3 = SentenceTransformer(L3, device="cpu")
ce = CrossEncoder(CE, device="cpu")
for name, m in ((L6, m6), (L3, m3)):
    mods = [type(x).__name__ for x in m]
    print(f"{name}: snapshot={snapshot(name)[:8]} modules={mods} max_seq_length={m.max_seq_length} "
          f"dim={m.get_embedding_dimension()}")
print(f"{CE}: snapshot={snapshot(CE)[:8]} max_seq_length={ce.max_seq_length} "
      f"tokenizer.model_max_length={ce.tokenizer.model_max_length} num_labels={ce.model.config.num_labels} "
      f"activation={type(ce.activation_fn).__name__ if hasattr(ce, 'activation_fn') else '?'}")

# ------------------------------------------------------------------ S2 toy 3-d vectors (hand computation)
head("S2 toy 3-d vectors (TOY ILLUSTRATION, hand-computable)")
q = np.array([1, 2, 2], float)
D = {"d1": np.array([2, 1, 2], float), "d2": np.array([0, 3, 4], float), "d3": np.array([2, 4, 4], float)}
print(f"q={q.tolist()} |q|={np.linalg.norm(q):.3f}")
rows = {}
for k, d in D.items():
    rows[k] = (float(q @ d), cos(q, d), l2(q, d))
    print(f"{k}={d.tolist()} |{k}|={np.linalg.norm(d):.3f}  dot={q @ d:.0f}  cos={cos(q, d):.4f}  L2={l2(q, d):.4f}  L2^2={l2(q, d)**2:.0f}")
rank = lambda key, rev: [k for k, _ in sorted(rows.items(), key=lambda kv: kv[1][key], reverse=rev)]
print("ranking by dot (high first):", rank(0, True))
print("ranking by cosine (high first):", rank(1, True))
print("ranking by raw L2 (low first):", rank(2, False))
print("-- after L2-normalising q and every d:")
qu = unit(q)
for k, d in D.items():
    du = unit(d)
    print(f"{k}: unit={np.round(du, 4).tolist()} dot={qu @ du:.4f} cos={cos(q, d):.4f} L2={l2(qu, du):.4f} "
          f"L2^2={l2(qu, du)**2:.4f} 2-2cos={2 - 2 * cos(q, d):.4f}")
nr = sorted(D, key=lambda k: l2(qu, unit(D[k])))
print("ranking by L2 on unit vectors (low first):", nr)
print("-- CR-08: scale ONE vector by 2")
d1x2 = 2 * D["d1"]
print(f"d1 -> 2*d1={d1x2.tolist()}: dot {q @ D['d1']:.0f} -> {q @ d1x2:.0f}; cos {cos(q, D['d1']):.4f} -> {cos(q, d1x2):.4f}; "
      f"L2 {l2(q, D['d1']):.4f} -> {l2(q, d1x2):.4f}")
qx2 = 2 * q
print(f"q -> 2*q={qx2.tolist()}: dots {[float(qx2 @ d) for d in D.values()]}, cos {[round(cos(qx2, d), 4) for d in D.values()]}, "
      f"L2 {[round(l2(qx2, d), 4) for d in D.values()]}")
print("   ranking by raw L2 with 2*q (low first):", sorted(D, key=lambda k: l2(qx2, D[k])))
print("-- dartboard-style distance 1 - dot on NON-unit vectors:", {k: 1 - float(q @ d) for k, d in D.items()})
print("-- dartboard-style distance 1 - dot on unit vectors:", {k: round(1 - float(qu @ unit(d)), 4) for k, d in D.items()})

# ------------------------------------------------------------------ S3 random vectors (04's proposed check)
head("S3 random vectors: cosine = dot after normalisation; L2 ranking = cosine ranking (TOY random data, seed 0)")
rng = np.random.default_rng(0)
N, NQ, DIM = 1000, 100, 384
X = rng.normal(size=(N, DIM))
Q = rng.normal(size=(NQ, DIM))
cosM = (Q @ X.T) / (np.linalg.norm(Q, axis=1)[:, None] * np.linalg.norm(X, axis=1)[None, :])
Xu, Qu = X / np.linalg.norm(X, axis=1, keepdims=True), Q / np.linalg.norm(Q, axis=1, keepdims=True)
dotU = Qu @ Xu.T
L2U = np.linalg.norm(Qu[:, None, :] - Xu[None, :, :], axis=2)
print(f"max |cos - dot(unit)| = {np.abs(cosM - dotU).max():.2e}")
print(f"max |L2^2 - (2 - 2cos)| on unit vectors = {np.abs(L2U**2 - (2 - 2 * cosM)).max():.2e}")
same_full = sum(np.array_equal(np.argsort(-cosM[i], kind="stable"), np.argsort(L2U[i], kind="stable")) for i in range(NQ))
print(f"queries whose FULL ranking of {N} docs is identical (cosine vs L2 on unit vectors): {same_full}/{NQ}")
scales = rng.uniform(0.5, 2.0, size=N)                     # give documents different lengths
Xs = X * scales[:, None]
L2raw = np.linalg.norm(Q[:, None, :] - Xs[None, :, :], axis=2)
dotraw = Q @ Xs.T
cosS = (Q @ Xs.T) / (np.linalg.norm(Q, axis=1)[:, None] * np.linalg.norm(Xs, axis=1)[None, :])
top_cos = cosS.argmax(1)
print(f"doc norms after scaling: min={np.linalg.norm(Xs, axis=1).min():.1f} max={np.linalg.norm(Xs, axis=1).max():.1f}")
print(f"queries where cosine top-1 is unchanged by the scaling: {(top_cos == cosM.argmax(1)).sum()}/{NQ}")
print(f"queries where raw-L2 top-1 != cosine top-1: {(L2raw.argmin(1) != top_cos).sum()}/{NQ}")
print(f"queries where raw-dot top-1 != cosine top-1: {(dotraw.argmax(1) != top_cos).sum()}/{NQ}")

# ------------------------------------------------------------------ S4 does the model output unit vectors?
head("S4 vector norms of real models on the 91 climate windows")
E6 = m6.encode(windows, convert_to_numpy=True, batch_size=32)            # default pipeline (with Normalize)
m6_raw = SentenceTransformer(modules=[m6[0], m6[1]], device="cpu")       # same weights, Normalize removed
E6raw = m6_raw.encode(windows, convert_to_numpy=True, batch_size=32)
E3 = m3.encode(windows, convert_to_numpy=True, batch_size=32)
for name, E in (("L6 default (Transformer,Pooling,Normalize)", E6), ("L6 without Normalize", E6raw), ("L3 default (no Normalize)", E3)):
    n = np.linalg.norm(E, axis=1)
    print(f"{name:44s} norm min={n.min():.6f} max={n.max():.6f} mean={n.mean():.4f}")
E6n = m6.encode(windows, convert_to_numpy=True, batch_size=32, normalize_embeddings=True)
print(f"L6: max |default - normalize_embeddings=True| = {np.abs(E6 - E6n).max():.2e}")
print(f"L6: max |default - unit(without Normalize)| = {np.abs(E6 - E6raw / np.linalg.norm(E6raw, axis=1, keepdims=True)).max():.2e}")
print(f"L6 dtype={E6.dtype} shape={E6.shape}")

# ------------------------------------------------------------------ S5 sentence pairs
head("S5 cosine of sentence pairs (all-MiniLM-L6-v2)")
PAIRS = [
    ("book-style pair", "greenhouse gas emissions", "carbon dioxide in the atmosphere"),
    ("book-style unrelated", "greenhouse gas emissions", "a recipe for chocolate cake"),
    ("paraphrase", "Burning coal and oil releases gases that warm the planet.",
     "Fossil fuel combustion emits greenhouse gases that heat the Earth."),
    ("unrelated", "Burning coal and oil releases gases that warm the planet.",
     "The museum opens at nine on Saturday mornings."),
    ("same words, opposite claim", "Global temperatures have risen since the late 19th century.",
     "Global temperatures have not risen since the late 19th century."),
]
for label, a, b in PAIRS:
    ea, eb = m6.encode([a, b], convert_to_numpy=True)
    print(f"{label:28s} cos={cos(ea, eb):.4f}  dot={float(ea @ eb):.4f}  L2={l2(ea, eb):.4f}  | {a!r} vs {b!r}")


# ------------------------------------------------------------------ S6 retrieval illustration on the climate windows
def norm_ws(s):
    return re.sub(r"\s+", " ", s)


QUESTIONS = {
    "D-002": ("In what year was the Paris Agreement adopted?", "adopted in 2015"),
    "D-004": ("What does DAC stand for, and what does it do?", "Direct air capture (DAC)"),
}
gold = {qid: [i for i, w in enumerate(windows) if key.lower() in norm_ws(w).lower()] for qid, (_, key) in QUESTIONS.items()}
head("S6 retrieval illustration: two seed questions x 91 windows (NOT an evaluation result)")
print("gold windows (contain the evidence phrase):", gold)


def topk(scores, k=5, low_is_best=False):
    order = np.argsort(scores if low_is_best else -scores, kind="stable")
    return [int(i) for i in order[:k]]


def rank_of(scores, idxs, low_is_best=False):
    order = list(np.argsort(scores if low_is_best else -scores, kind="stable"))
    return min(order.index(i) + 1 for i in idxs)


for qid, (qtext, _) in QUESTIONS.items():
    print(f"-- {qid}: {qtext!r}")
    q6 = m6.encode([qtext], convert_to_numpy=True)[0]
    q6raw = m6_raw.encode([qtext], convert_to_numpy=True)[0]
    q3 = m3.encode([qtext], convert_to_numpy=True)[0]
    c6 = E6 @ q6                                            # unit vectors: dot = cosine
    l6 = np.linalg.norm(E6 - q6, axis=1)
    print(f"  shapes: query {q6.shape}, index {E6.shape}, scores {c6.shape} (one score per window; an all-pairs matrix would be "
          f"{len(windows)}x{len(windows)} = {len(windows)**2})")
    print(f"  L6 normalised : cosine top5={topk(c6)} gold rank={rank_of(c6, gold[qid])} | L2 top5={topk(l6, low_is_best=True)} "
          f"| max |L2^2-(2-2cos)|={np.abs(l6**2 - (2 - 2 * c6)).max():.2e} | top1 cos={c6.max():.4f}")
    c6r = np.array([cos(q6raw, e) for e in E6raw])
    l6r = np.linalg.norm(E6raw - q6raw, axis=1)
    d6r = E6raw @ q6raw
    print(f"  L6 raw (no Normalize): cosine top5={topk(c6r)} | raw L2 top5={topk(l6r, low_is_best=True)} gold rank={rank_of(l6r, gold[qid], True)}"
          f" | raw dot top5={topk(d6r)} gold rank={rank_of(d6r, gold[qid])}")
    c3 = np.array([cos(q3, e) for e in E3])
    l3 = np.linalg.norm(E3 - q3, axis=1)
    d3 = E3 @ q3
    print(f"  L3 (own index): cosine top5={topk(c3)} gold rank={rank_of(c3, gold[qid])} | raw L2 top5={topk(l3, low_is_best=True)} "
          f"gold rank={rank_of(l3, gold[qid], True)} | raw dot top5={topk(d3)} gold rank={rank_of(d3, gold[qid])}")
    mix = E6 @ unit(q3)                                     # query from L3, documents from L6: same dim 384, no error
    print(f"  WRONG MODEL (query L3, docs L6, dims {q3.shape[0]}=={E6.shape[1]}): cosine top5={topk(mix)} gold rank={rank_of(mix, gold[qid])} "
          f"| cos range {mix.min():.4f}..{mix.max():.4f} (right model: {c6.min():.4f}..{c6.max():.4f}) | errors raised: none")

# ------------------------------------------------------------------ S7 04's truncation experiment: the answer in the tail
head("S7 truncation vs its question (04 P4 experiment; mechanism already in P1 D.4)")
tok = m6.tokenizer
key = "Direct air capture (DAC)"
pos = norm_ws(full).find(key)
nf = norm_ws(full)
enc = tok(nf, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
offs = enc["offset_mapping"]
key_tok = next(i for i, (a, b) in enumerate(offs) if a >= pos)
start_tok = key_tok - 300                                   # place the DAC sentence at text token 300 (past the 254 cap)
long_text = nf[offs[start_tok][0]:offs[start_tok + 400 - 1][1]]
prefix = nf[offs[start_tok][0]:offs[start_tok + 254 - 1][1]]
tail = nf[offs[start_tok + 254][0]:offs[start_tok + 400 - 1][1]]
cnt = lambda t: len(tok(t, add_special_tokens=False)["input_ids"])
print(f"passage tokens={cnt(long_text)} prefix tokens={cnt(prefix)} tail tokens={cnt(tail)}; "
      f"DAC phrase starts at text token {key_tok - start_tok}; in prefix? {key in prefix}; in long_text? {key in long_text}")
qv = m6.encode([QUESTIONS['D-004'][0]], convert_to_numpy=True)[0]
el, ep, et = m6.encode([long_text, prefix, tail], convert_to_numpy=True)
print(f"cos(D-004 question, 400-token passage) = {float(qv @ el):.6f}")
print(f"cos(D-004 question, its 254-token prefix) = {float(qv @ ep):.6f}")
print(f"cos(D-004 question, the tail tokens 255-400, embedded alone) = {float(qv @ et):.6f}")

# ------------------------------------------------------------------ S8 bi-encoder vs cross-encoder
head("S8 bi-encoder (L6) shortlist vs cross-encoder rerank (NOT an evaluation result)")
calls = {"bi_doc_encodes_once": len(windows)}
for qid, (qtext, _) in QUESTIONS.items():
    q6 = m6.encode([qtext], convert_to_numpy=True)[0]
    c6 = E6 @ q6
    short = topk(c6, 10)
    ce_short = ce.predict([(qtext, windows[i]) for i in short])
    rer = [short[i] for i in np.argsort(-ce_short, kind="stable")]
    ce_all = ce.predict([(qtext, w) for w in windows])
    print(f"-- {qid}: bi top10={short}")
    print(f"   cross-encoder scores on the shortlist: min={ce_short.min():.3f} max={ce_short.max():.3f} (raw logits, not bounded like cosine)")
    print(f"   reranked top3={rer[:3]} | gold={gold[qid]} | bi rank of first gold={rank_of(c6, gold[qid])} "
          f"| CE-over-shortlist rank={min(rer.index(g) + 1 for g in gold[qid] if g in rer) if any(g in rer for g in gold[qid]) else 'not in shortlist'}"
          f" | CE over all 91 top3={topk(ce_all, 3)} rank of first gold={rank_of(ce_all, gold[qid])}")
    print(f"   forward passes per query: bi-encoder 1 (query) + 0 (docs precomputed) ; cross-encoder rerank {len(short)} ; cross-encoder over all {len(windows)}")
    sw = ce.predict([(windows[short[0]], qtext)])[0]
    print(f"   order check: CE(q, d)={ce.predict([(qtext, windows[short[0]])])[0]:.3f} vs CE(d, q)={sw:.3f}")
print(f"bi-encoder document encodes, done once at index time: {calls['bi_doc_encodes_once']}")
print("cross-encoder has no stored vector per document: nothing can be precomputed for an unseen query")

# ------------------------------------------------------------------ S9 asymmetry
head("S9 query/document asymmetry (single illustrations, not evaluations)")
qtext = QUESTIONS["D-002"][0]
stmt = "The Paris Agreement was adopted in 2015."
g = gold["D-002"][0]
eq, es, ew = m6.encode([qtext, stmt, windows[g]], convert_to_numpy=True)
print(f"gold window {g}: cos(question, window)={float(eq @ ew):.4f}  cos(statement-shaped text, window)={float(es @ ew):.4f}  "
      f"cos(question, statement)={float(eq @ es):.4f}")
for pre in ("query: ", "search_query: ", "Represent this sentence for searching relevant passages: "):
    a, b = m6.encode([pre + qtext, qtext], convert_to_numpy=True)
    print(f"MiniLM (trained without prefixes): cos({pre!r}+q, q) = {float(a @ b):.4f}")
qa = m6.encode(["query: " + qtext], convert_to_numpy=True)[0]
print(f"rank of gold window with prefix 'query: ' = {rank_of(E6 @ qa, gold['D-002'])} (without prefix: {rank_of(E6 @ eq, gold['D-002'])})")

# ------------------------------------------------------------------ S10 the graph_rag inversion (toy)
head("S10 graph_rag.ipynb cell 12 priority = 1 / score (TOY numbers)")
nodes = {"A": 0.20, "B": 0.50, "C": 0.90}
for label, meaning in (("if score is a DISTANCE (lower = closer)", "distance"), ("if score is a SIMILARITY (higher = closer)", "similarity")):
    h = []
    for n, s in nodes.items():
        heapq.heappush(h, (1 / s, n))
    order = [heapq.heappop(h)[1] for _ in range(len(h))]
    closest = min(nodes, key=nodes.get) if meaning == "distance" else max(nodes, key=nodes.get)
    print(f"scores {nodes}; {label}: min-heap pops {order}; the closest node is {closest}; explored {order.index(closest) + 1} of 3")
try:
    1 / 0.0
except ZeroDivisionError as ex:
    print("score 0.0 (an exact duplicate under a distance) -> ZeroDivisionError:", ex)
print("\nDONE")
