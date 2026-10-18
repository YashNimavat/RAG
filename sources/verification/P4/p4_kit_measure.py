"""P4 study-kit measurements (K1-K13): the numbers the HTML lesson adds on top of p4_measure.py (S1-S10).

Why a second script: the study kit uses v0's **97 chunks** (the 07 recursive chunker, per page, 1000/200, as in
P3's verify notebook and R1), while p4_measure.py measured the old 91 plain windows. p4_measure.py is not changed,
so its saved output stays byte-identical. Numbers that do not depend on chunking (S2, S3, S5, S7, S9 prefixes,
S10) are reused from P4_FACTS section 1 and not repeated here, except where a lesson table needs them side by side.

Local only: no Groq, Cohere or Claude call, no .env read. Models load from the local Hugging Face cache (offline).
Labels: the draft seeds of 06 section 6.7 are LLM-drafted and not human-verified: every rank below is an
observation on draft seeds, never an evaluation result.

Run from rag_learning/:
    uv run python sources/verification/P4/p4_kit_measure.py "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
Saved output: sources/verification/P4/out_p4_kit_measure.txt  (sections K1..K13 for P4_FACTS.md section 1b)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import hashlib
import importlib.metadata as md
import json
import logging
import math
import sys
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7

PDF = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
L6 = "sentence-transformers/all-MiniLM-L6-v2"
L3 = "sentence-transformers/paraphrase-MiniLM-L3-v2"
CE = "cross-encoder/ms-marco-MiniLM-L-6-v2"
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)


def head(t):
    print(f"\n=== {t}")


def f4(x):
    return f"{x:.4f}"


def snapshot(repo_id):
    ref = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{repo_id.replace('/', '--')}" / "refs" / "main"
    return ref.read_text().strip() if ref.exists() else "?"


# ---------------------------------------------------------------- the 97 chunks and the draft seeds (as P3 verify)
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
SHA_JL = hashlib.sha256("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")).hexdigest()
TEXT = [c["text"] for c in chunks]
PAGE = [c["page_segments"][0]["page"] for c in chunks]
N = len(chunks)
TEXTS = {"climate": "\n".join(pages)}
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines()
         if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
REL = {s["qid"]: [i for i in range(N) if cc.rel(("climate", chunks[i]["char_start"], chunks[i]["char_end"]), s["G"], TEXTS)]
       for s in ANS}


def order(scores, low_is_best=False):
    """chunk seqs best first; ties broken by the smaller seq (the course rule)."""
    s = np.asarray(scores, float)
    return sorted(range(len(s)), key=lambda i: ((s[i] if low_is_best else -s[i]), i))


def first_rel(ranking, qid):
    return next((r for r, i in enumerate(ranking, 1) if i in REL[qid]), None)


def summary(ranks, k=4):
    """Hit@1, Hit@k (counts) and MRR@10 over a list of first-relevant ranks."""
    hit1 = sum(r is not None and r <= 1 for r in ranks)
    hitk = sum(r is not None and r <= k for r in ranks)
    mrr = sum(1 / r for r in ranks if r is not None and r <= 10) / len(ranks)
    return hit1, hitk, round(mrr, 3)


def unit(M):
    M = np.asarray(M, float)
    return M / np.linalg.norm(M, axis=-1, keepdims=True)


# ---------------------------------------------------------------- K1
head("K1 environment, corpus, models")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "sentence-transformers", "transformers", "torch", "numpy", "tokenizers")})
print("pdf sha256", hashlib.sha256(pdf_bytes).hexdigest())
print(f"97 chunks: count={N} chunks.jsonl sha256={SHA_JL} (P3 verify / C2 lab: d4108b89...)")
print(f"draft seeds: {len(SEEDS)} ({len(ANS)} answerable); relevant chunk seqs per answerable seed: {REL}")

from sentence_transformers import CrossEncoder, SentenceTransformer  # noqa: E402
from sentence_transformers.util import quantize_embeddings          # noqa: E402

m6 = SentenceTransformer(L6, device="cpu")
m3 = SentenceTransformer(L3, device="cpu")
ce = CrossEncoder(CE, device="cpu")
m6_raw = SentenceTransformer(modules=[m6[0], m6[1]], device="cpu")      # same weights, Normalize removed
for name, m in ((L6, m6), (L3, m3)):
    print(f"{name}: snapshot={snapshot(name)[:8]} modules={[type(x).__name__ for x in m]} max_seq_length={m.max_seq_length} "
          f"dim={m.get_embedding_dimension()} similarity_fn_name={m.similarity_fn_name!r} prompts={m.prompts!r}")
print(f"{L6} pooling config: mean_tokens={m6[1].pooling_mode_mean_tokens if hasattr(m6[1], 'pooling_mode_mean_tokens') else m6[1].get_config_dict()}")
print(f"{CE}: snapshot={snapshot(CE)[:8]} max_seq_length={ce.max_seq_length}")


def enc(model, texts, **kw):
    return model.encode(list(texts), convert_to_numpy=True, batch_size=32, show_progress_bar=False, **kw)


E6 = enc(m6, TEXT)
E6raw = enc(m6_raw, TEXT)
E3 = enc(m3, TEXT)
Q6 = {s["qid"]: enc(m6, [s["question"]])[0] for s in SEEDS}
Q6raw = {s["qid"]: enc(m6_raw, [s["question"]])[0] for s in SEEDS}
Q3 = {s["qid"]: enc(m3, [s["question"]])[0] for s in SEEDS}

# ---------------------------------------------------------------- K2
head("K2 vector lengths on the 97 chunks")
for name, E in (("L6 default (Transformer, Pooling, Normalize)", E6), ("L6 with Normalize removed", E6raw),
                ("L3 default (no Normalize)", E3)):
    n = np.linalg.norm(E, axis=1)
    print(f"{name:46s} norm min={n.min():.6f} max={n.max():.6f} mean={n.mean():.4f}")
print(f"L6 max |norm - 1| = {np.abs(np.linalg.norm(E6, axis=1) - 1).max():.2e}; dtype={E6.dtype} shape={E6.shape}")
print(f"bytes per vector: float32 {E6.shape[1] * 4}; whole index {E6.nbytes} bytes")

# ---------------------------------------------------------------- K3
head("K3 D-002 on the 97 chunks: one score per chunk; the wrong-model bug")
q = Q6["D-002"]
c6 = E6 @ q
l6 = np.linalg.norm(E6 - q, axis=1)
o = order(c6)
print(f"question: {BYQ['D-002']['question']!r}; relevant seqs {REL['D-002']} (page {[PAGE[i] for i in REL['D-002']]})")
print(f"shapes: query {q.shape}, index {E6.shape}, scores {c6.shape}; an all-pairs matrix would be {N}x{N} = {N * N}")
print(f"L6 cosine top5={o[:5]} scores={[f4(c6[i]) for i in o[:5]]} first relevant rank={first_rel(o, 'D-002')}")
print(f"L6 L2 on unit vectors top5={order(l6, True)[:5]} | identical full ranking={order(l6, True) == o} "
      f"| max |L2^2-(2-2cos)|={np.abs(l6 ** 2 - (2 - 2 * c6)).max():.2e}")
cr = unit(E6raw) @ unit(Q6raw["D-002"])
lr = np.linalg.norm(E6raw - Q6raw["D-002"], axis=1)
dr = E6raw @ Q6raw["D-002"]
print(f"L6 raw (no Normalize): cosine top5={order(cr)[:5]} | raw L2 top5={order(lr, True)[:5]} rank={first_rel(order(lr, True), 'D-002')}"
      f" | raw dot top5={order(dr)[:5]} rank={first_rel(order(dr), 'D-002')}")
mix = E6 @ unit(Q3["D-002"])
print(f"WRONG MODEL (query L3, chunks L6; both {Q3['D-002'].shape[0]}-d; no error raised): top5={order(mix)[:5]} "
      f"first relevant rank={first_rel(order(mix), 'D-002')} | cos range {mix.min():.4f}..{mix.max():.4f} "
      f"(right model {c6.min():.4f}..{c6.max():.4f})")
c3own = unit(E3) @ unit(Q3["D-002"])
print(f"L3 with its OWN index: top5={order(c3own)[:5]} first relevant rank={first_rel(order(c3own), 'D-002')}")

# ---------------------------------------------------------------- K4
head("K4 the 8 answerable draft seeds: right model, wrong model, other model (Hit@1, Hit@4 counts of 8; MRR@10)")
ARMS = {
    "L6 cosine (right)": {s["qid"]: E6 @ Q6[s["qid"]] for s in ANS},
    "wrong model: L3 query vs L6 chunks": {s["qid"]: E6 @ unit(Q3[s["qid"]]) for s in ANS},
    "L3 query vs L3 chunks (a different model, used correctly)": {s["qid"]: unit(E3) @ unit(Q3[s["qid"]]) for s in ANS},
    "L6 raw vectors, raw dot": {s["qid"]: E6raw @ Q6raw[s["qid"]] for s in ANS},
    "L6 raw vectors, raw L2 (low first)": {s["qid"]: -np.linalg.norm(E6raw - Q6raw[s["qid"]], axis=1) for s in ANS},
}
RANKS = {}
for arm, sc in ARMS.items():
    ranks = [first_rel(order(sc[s["qid"]]), s["qid"]) for s in ANS]
    RANKS[arm] = ranks
    print(f"{arm:58s} ranks D-001..D-008={ranks} Hit@1,Hit@4,MRR@10={summary(ranks)}")
top1 = {s["qid"]: float((E6 @ Q6[s["qid"]]).max()) for s in SEEDS}
print("L6 top-1 cosine per seed:", {k: f4(v) for k, v in top1.items()})
print(f"answerable top-1 range {min(top1[s['qid']] for s in ANS):.4f}..{max(top1[s['qid']] for s in ANS):.4f}; "
      f"unanswerable D-009 {top1['D-009']:.4f}, D-010 {top1['D-010']:.4f}")

# ---------------------------------------------------------------- K5
head("K5 score direction: one pair, every library convention (book's unrelated pair; and D-002 over 97 chunks)")
a, b = enc(m6, ["greenhouse gas emissions", "a recipe for chocolate cake"])
cab = float(a @ b)
L = float(np.linalg.norm(a - b))
m6.similarity_fn_name = "euclidean"
st_euc = float(m6.similarity(a[None], b[None])[0][0])
m6.similarity_fn_name = "cosine"
st_cos = float(m6.similarity(a[None], b[None])[0][0])
print(f"cosine={cab:.4f} | L2={L:.4f} | squared L2 (what FAISS IndexFlatL2 returns)={L * L:.4f} | 2-2cos={2 - 2 * cab:.4f}")
print(f"sentence-transformers similarity(): cosine={st_cos:.4f}; euclidean={st_euc:.4f} (= -L2)")
print(f"LangChain Euclidean relevance 1 - d/sqrt(2): on true L2 {1 - L / math.sqrt(2):.4f}; on squared L2 (FAISS) {1 - L * L / math.sqrt(2):.4f}")
print(f"worst case (opposite unit vectors, squared L2 = 4): {1 - 4 / math.sqrt(2):.4f}; on true L2 = 2: {1 - 2 / math.sqrt(2):.4f}")
print(f"relevance on squared L2 is negative when cos < 1 - 1/sqrt(2) = {1 - 1 / math.sqrt(2):.4f}; on true L2 when cos < 0")
c = E6 @ Q6["D-002"]
print(f"D-002 over 97 chunks: cos min={c.min():.4f} max={c.max():.4f}; chunks with cos < 0.2929 (negative LangChain relevance "
      f"on FAISS squared L2): {int((c < 1 - 1 / math.sqrt(2)).sum())} of {N}; chunks with cos < 0: {int((c < 0).sum())}")
print(f"self-retrieval check on chunk 0: cos(chunk, itself)={float(E6[0] @ E6[0]):.6f}; "
      f"L2={float(np.linalg.norm(E6[0] - E6[0])):.6f}; its rank among {N} = {order(E6 @ E6[0]).index(0) + 1}")
selfrank = [order(E6 @ E6[i])[0] == i for i in range(N)]
print(f"every chunk ranks itself first (cosine): {sum(selfrank)}/{N}")

# ---------------------------------------------------------------- K6
head("K6 score scale: what a 'good' cosine looks like here (MiniLM L6)")
med = {s["qid"]: float(np.median(E6 @ Q6[s["qid"]])) for s in SEEDS}
print("median cosine over the 97 chunks, per seed:", {k: f4(v) for k, v in med.items()})
allq = np.concatenate([E6 @ Q6[s["qid"]] for s in SEEDS])
print(f"all 10 seeds x 97 chunks = {allq.size} question-chunk scores: min={allq.min():.4f} p50={np.median(allq):.4f} "
      f"p90={np.percentile(allq, 90):.4f} max={allq.max():.4f}")
C = E6 @ E6.T
off = C[~np.eye(N, dtype=bool)]
iu = np.triu_indices(N, 1)
pairs = C[iu]
print(f"all-pairs analysis (chunk vs chunk, {N}x{N}, {len(pairs)} distinct pairs): min={pairs.min():.4f} p50={np.median(pairs):.4f} "
      f"max={pairs.max():.4f}; pairs with cos > 0.98: {int((pairs > 0.98).sum())}; > 0.90: {int((pairs > 0.90).sum())}")
j = int(np.argmax(pairs))
print(f"closest pair: seqs {int(iu[0][j])} and {int(iu[1][j])} (pages {PAGE[iu[0][j]]}, {PAGE[iu[1][j]]}) cos={pairs[j]:.4f}")
hist = np.histogram(pairs, bins=np.arange(-0.2, 1.0001, 0.1))
print("histogram of the distinct pairs (bin edges -0.2..1.0 by 0.1):", hist[0].tolist())
SPAIRS = [("greenhouse gas emissions", "carbon dioxide in the atmosphere"),
          ("greenhouse gas emissions", "a recipe for chocolate cake"),
          ("Global temperatures have risen since the late 19th century.",
           "Global temperatures have not risen since the late 19th century.")]
for x, y in SPAIRS:
    ex, ey = enc(m6, [x, y])
    print(f"S5 re-check: cos({x!r}, {y!r}) = {float(ex @ ey):.4f}")

# ---------------------------------------------------------------- K7
head("K7 length limit: the 97 chunks against MiniLM's 256-token cap (own tokenizer, [CLS]/[SEP] included)")
tok = m6.tokenizer
ntok = [len(tok(t, add_special_tokens=True)["input_ids"]) for t in TEXT]
over = [i for i, n in enumerate(ntok) if n > m6.max_seq_length]
print(f"tokens per chunk: min={min(ntok)} median={int(np.median(ntok))} max={max(ntok)}; over {m6.max_seq_length}: {len(over)} of {N} {over}")
if over:
    for i in over:
        ids = tok(TEXT[i], add_special_tokens=False, return_offsets_mapping=True)
        cut = ids["offset_mapping"][m6.max_seq_length - 2 - 1][1]
        print(f"  seq {i} (page {PAGE[i]}): {ntok[i]} tokens; characters read {cut} of {len(TEXT[i])}; "
              f"ignored {len(TEXT[i]) - cut}")
print(f"L6 was trained on sequences of at most 128 tokens (model card): chunks longer than 128: {sum(n > 128 for n in ntok)} of {N}")
ntok3 = [len(m3.tokenizer(t, add_special_tokens=True)["input_ids"]) for t in TEXT]
print(f"L3 (own tokenizer) max_seq_length={m3.max_seq_length}: chunks over it: {sum(n > m3.max_seq_length for n in ntok3)} of {N}; "
      f"same token counts as L6's tokenizer: {ntok3 == ntok}")
print(f"chars per chunk: min={min(map(len, TEXT))} median={int(np.median(list(map(len, TEXT))))} max={max(map(len, TEXT))}")

# ---------------------------------------------------------------- K8
head("K8 asymmetry: encode_query / encode_document, and question vs statement")
qq = m6.encode_query([s["question"] for s in SEEDS], convert_to_numpy=True, show_progress_bar=False)
qe = enc(m6, [s["question"] for s in SEEDS])
dd = m6.encode_document(TEXT[:10], convert_to_numpy=True, show_progress_bar=False)
print(f"MiniLM prompts={m6.prompts!r}; max |encode_query - encode| = {np.abs(qq - qe).max():.1e}; "
      f"max |encode_document - encode| (10 chunks) = {np.abs(dd - E6[:10]).max():.1e}")
g = REL["D-002"][0]
stmt = "The Paris Agreement was adopted in 2015."
eq, es = enc(m6, [BYQ["D-002"]["question"], stmt])
print(f"D-002 relevant chunk seq {g}: cos(question, chunk)={float(eq @ E6[g]):.4f}; cos(statement, chunk)={float(es @ E6[g]):.4f}; "
      f"cos(question, statement)={float(eq @ es):.4f}")
o_stmt = order(E6 @ es)
print(f"rank of seq {g}: with the question {first_rel(order(E6 @ eq), 'D-002')}; with the statement-shaped text {first_rel(o_stmt, 'D-002')}")

# ---------------------------------------------------------------- K9
head("K9 bi-encoder shortlist (top-10) vs cross-encoder rerank, 97 chunks (illustration, not an evaluation)")
q = BYQ["D-002"]["question"]
o = order(E6 @ Q6["D-002"])
short = o[:10]
cs = ce.predict([(q, TEXT[i]) for i in short], show_progress_bar=False)
rer = [short[i] for i in np.argsort(-cs, kind="stable")]
print(f"D-002 bi top10={short}; CE logits min={cs.min():.3f} max={cs.max():.3f}; reranked top3={rer[:3]}; "
      f"first relevant rank bi {first_rel(o, 'D-002')} -> CE {first_rel(rer, 'D-002')}")
print(f"order matters: CE(q, d)={float(ce.predict([(q, TEXT[short[0]])], show_progress_bar=False)[0]):.3f} vs "
      f"CE(d, q)={float(ce.predict([(TEXT[short[0]], q)], show_progress_bar=False)[0]):.3f} (seq {short[0]})")
print(f"model passes per question: bi-encoder 1 (the question; {N} chunk vectors stored at index time); "
      f"cross-encoder 10 to rerank a top-10, {N} to score every chunk")
bi_r, ce_r, all_r = [], [], []
for s in ANS:
    ob = order(E6 @ Q6[s["qid"]])
    sh = ob[:10]
    sc = ce.predict([(s["question"], TEXT[i]) for i in sh], show_progress_bar=False)
    rr = [sh[i] for i in np.argsort(-sc, kind="stable")] + ob[10:]
    sa = ce.predict([(s["question"], t) for t in TEXT], show_progress_bar=False)
    bi_r.append(first_rel(ob, s["qid"]))
    ce_r.append(first_rel(rr, s["qid"]))
    all_r.append(first_rel(order(sa), s["qid"]))
print(f"8 seeds first relevant rank: bi {bi_r} {summary(bi_r)} | bi top-10 + CE rerank {ce_r} {summary(ce_r)} | "
      f"CE over all 97 {all_r} {summary(all_r)}")

# ---------------------------------------------------------------- K10
head("K10 how the embedder learned: a toy training batch (B = 4 question/chunk pairs; TOY illustration)")
B = ["D-002", "D-004", "D-006", "D-008"]
Qb = np.stack([Q6[k] for k in B])
Pb = np.stack([E6[REL[k][0]] for k in B])
Sb = Qb @ Pb.T
print(f"pairs: {[(k, REL[k][0]) for k in B]}")
print("S = Q P^T (rows: questions, columns: chunks):")
for k, row in zip(B, Sb):
    print(f"  {k}: {[f4(v) for v in row]}  row max on the diagonal: {int(np.argmax(row)) == B.index(k)}")
for scale in (1, 20):
    z = Sb * scale
    lsm = z - np.log(np.exp(z).sum(1, keepdims=True))
    p = np.exp(lsm)
    print(f"scale {scale:2d} (tau = {1 / scale:g}): softmax weight on the true pair per row {[f4(v) for v in np.diag(p)]}; "
          f"mean loss -log p = {float(-np.mean(np.diag(lsm))):.4f}")
z = (Qb @ Pb[[1, 2, 3, 0]].T) * 20
lsm = z - np.log(np.exp(z).sum(1, keepdims=True))
print(f"same batch with the chunks shuffled (wrong 'true' pairs), scale 20: mean loss {float(-np.mean(np.diag(lsm))):.4f}")

# ---------------------------------------------------------------- K11
head("K11 cutting dimensions (MiniLM is NOT Matryoshka-trained): lengths and ranks on the 8 seeds")
for d in (384, 256, 128, 64, 32):
    Ed = enc(m6, TEXT, truncate_dim=d)
    Qd = {s["qid"]: enc(m6, [s["question"]], truncate_dim=d)[0] for s in ANS}
    nrm = np.linalg.norm(Ed, axis=1)
    cos_r = [first_rel(order(unit(Ed) @ unit(Qd[s["qid"]])), s["qid"]) for s in ANS]
    dot_r = [first_rel(order(Ed @ Qd[s["qid"]]), s["qid"]) for s in ANS]
    same5 = sum(order(Ed @ Qd[s["qid"]])[:5] == order(unit(Ed) @ unit(Qd[s["qid"]]))[:5] for s in ANS)
    print(f"dim {d:3d}: chunk norms {nrm.min():.4f}..{nrm.max():.4f} | renormalised cosine ranks {cos_r} {summary(cos_r)} "
          f"| raw dot without renormalising ranks {dot_r} {summary(dot_r)} | top-5 identical dot vs cosine: {same5}/8 "
          f"| bytes float32 {d * 4}")

# ---------------------------------------------------------------- K12
head("K12 compressed vectors: int8 and binary vs float32 (8 seeds; top-5 overlap with float32)")
QA = np.stack([Q6[s["qid"]] for s in ANS])
ranges = np.vstack((E6.min(0), E6.max(0)))
E8 = quantize_embeddings(E6, "int8", ranges=ranges)
Q8 = quantize_embeddings(QA, "int8", ranges=ranges)
Eb = quantize_embeddings(E6, "ubinary")
Qb_ = quantize_embeddings(QA, "ubinary")
print(f"bytes per vector: float32 {E6[0].nbytes}, int8 {E8[0].nbytes}, ubinary {Eb[0].nbytes}; dtypes {E8.dtype} {Eb.dtype}")
bits_E = np.unpackbits(Eb, axis=1)
o_ranks = {"int8": [], "binary": []}
ov = {"int8": [], "binary": []}
for j, s in enumerate(ANS):
    of = order(E6 @ QA[j])
    o8 = order(E8.astype(np.int32) @ Q8[j].astype(np.int32))
    ham = (bits_E != np.unpackbits(Qb_[j][None], axis=1)).sum(1)
    ob = order(ham, low_is_best=True)
    for key, oo in (("int8", o8), ("binary", ob)):
        o_ranks[key].append(first_rel(oo, s["qid"]))
        ov[key].append(len(set(oo[:5]) & set(of[:5])))
    if s["qid"] == "D-002":
        print(f"D-002 top5: float {of[:5]} | int8 {o8[:5]} | binary (Hamming) {ob[:5]}")
print(f"float32 ranks {RANKS['L6 cosine (right)']} {summary(RANKS['L6 cosine (right)'])}")
for key in ("int8", "binary"):
    print(f"{key:6s} ranks {o_ranks[key]} {summary(o_ranks[key])} | top-5 overlap with float per seed {ov[key]} "
          f"(mean {np.mean(ov[key]):.2f} of 5)")

# ---------------------------------------------------------------- K13
head("K13 formula arithmetic for the lesson (FORMULA; the Cohere price is UNVERIFIED)")
for n in (97, 1000, 10000):
    print(f"Cohere calls for {n} texts at <= 96 per call: ceil({n}/96) = {math.ceil(n / 96)}")
print(f"10,000 chunks x 250 tokens = {10000 * 250:,} tokens; at $0.12 per 1M tokens (UNVERIFIED) = ${10000 * 250 * 0.12 / 1e6:.2f}")
for d, label in ((1536, "Cohere default"), (1024, ""), (512, ""), (256, ""), (384, "MiniLM")):
    print(f"dim {d:4d} {label:14s}: float32 {d * 4:5d} B, int8 {d:4d} B, binary {d // 8:3d} B per vector")
n = 2_000_000
for d, by, label in ((1536, 4, "float32 1536"), (1536, 1, "int8 1536"), (1536, 1 / 8, "binary 1536"), (256, 4, "float32 256")):
    tot = n * d * by
    print(f"2,000,000 x {label:13s} = {tot / 1e9:.3f} GB ({tot / 2**30:.2f} GiB)")
print("\nDONE")
