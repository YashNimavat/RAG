"""R1 (sparse vs dense vs hybrid; fusion) measurements: every number in concepts/R1_hybrid_fusion.md and
study/reading/R1_hybrid_fusion.md comes from this run, from arithmetic shown in the lesson, or carries a label.

Local only: no Groq or Cohere call, no .env read, no network. MiniLM loads from the local Hugging Face cache (offline).
Corpus D and the v0 index are rebuilt exactly as C3/C4 do (06 §3.1): PyMuPDF 1.26.7 page.get_text(), pages joined
with "\\n", the 07 H.1/H.3 recursive chunker (executed from 07, as the acceptance suite does), per_page, 1000/200,
course chunk ids (params_hash 1ca9c5a3b548), MiniLM all-MiniLM-L6-v2, normalised, float32. BM25: rank_bm25 0.2.2
BM25Okapi with P3's tok_norm (and the repo's split() for comparison). Gold: the 10 DRAFT seeds of 06 §6.7
(llm-draft): every seed number is a draft-seed observation, never an evaluation result.

This file is a REFERENCE SOLUTION for labs/R1_hybrid_fusion_lab.ipynb. Do not show it before an attempt (CR-04).

Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/R1/r1_measure.py \
        "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        > sources/verification/R1/out_r1_measure.txt 2> sources/verification/R1/out_r1_measure.stderr.txt
Sections S1..S14 are deterministic (two runs are diffed in R1_FACTS.md). Lines starting "FP " are lab fingerprints.
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import hashlib
import importlib.metadata as md
import json
import math
import re
import statistics as st
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pymupdf
from rank_bm25 import BM25Okapi

PDF = sys.argv[1]
WS = Path(__file__).resolve().parents[3]                      # rag_learning/
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                                  # noqa: E402  (reference rel / ce / 07 loader)

MINILM = "sentence-transformers/all-MiniLM-L6-v2"
K = 4                                                         # v0 k (06 §3.1)
N_LIST = 50                                                   # per-retriever list depth (06 v2.0 card: top-50)
K_RRF = 60                                                    # Cormack et al. 2009 (06 v2.0 card, Source C #33)


def head(t):
    print(f"\n=== {t}")


def fp(x):                                                    # same fingerprint as the lab's _fp
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


def emit(name, value):
    print(f"FP {name} {fp(value)}")


# ================================================================ the functions the lesson teaches (reference)
NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")


def tok_norm(text):                                           # P3's tokenizer (P3 K): lower-case, keeps 1.5 whole
    return NORM_RE.findall(text.lower())


def tok_split(text):                                          # the repo's tokenizer (fusion_retrieval.ipynb cells 14, 17)
    return text.split()


def order(scores):
    """ids best first; ties broken by the smaller id (06 §3.1). `scores` is a dict id -> float."""
    return sorted(scores, key=lambda d: (-scores[d], d))


def top_list(scores, n, positive_only=False):
    """The top-n of one retriever as a dict id -> raw score. BM25 keeps only score > 0 (P3 K: 0 = no term matched)."""
    ids = [d for d in order(scores) if (scores[d] > 0 or not positive_only)][:n]
    return {d: scores[d] for d in ids}


def rrf(ranked_lists, k=K_RRF):
    """Reciprocal Rank Fusion: sum over lists of 1/(k + rank), ranks from 1. A missing id adds nothing."""
    fused = {}
    for lst in ranked_lists:
        for r, d in enumerate(lst, 1):
            fused[d] = fused.get(d, 0.0) + 1.0 / (k + r)
    return fused


def minmax(s):
    """Min-max over ONE list (dict id -> score). Constant list: every member is that list's best, so 1.0 (course rule)."""
    if not s:
        return {}
    lo, hi = min(s.values()), max(s.values())
    if hi == lo:
        return {d: 1.0 for d in s}
    return {d: (v - lo) / (hi - lo) for d, v in s.items()}


def zscore3(s, ddof=0):
    """Book Ch12 p.8/14 / llamaindex cell 20 'dist_based_score' form: (x - (mu - 3 sd)) / (6 sd). Not clipped.
    ddof=0: population sd. A constant list gives 0.5 (the limit of the formula as sd -> 0)."""
    if not s:
        return {}
    v = np.array(list(s.values()), dtype=float)
    mu, sd = float(v.mean()), float(v.std(ddof=ddof)) if len(v) > ddof else 0.0
    if sd == 0:
        return {d: 0.5 for d in s}
    return {d: (x - (mu - 3 * sd)) / (6 * sd) for d, x in s.items()}


def weighted(lists, weights, norm):
    """Weighted score fusion over ALIGNED ids: each list is a dict id -> raw score; normalise each list on its own;
    a chunk missing from a list gets 0 from it (book Ch12 p.9/14). Returns dict id -> fused score."""
    normed = {name: norm(lst) for name, lst in lists.items()}
    ids = set().union(*[set(x) for x in normed.values()])
    return {d: sum(weights[name] * normed[name].get(d, 0.0) for name in normed) for d in ids}


# ================================================================ S1 environment, snapshot, v0 index
head("S1 environment, snapshot, v0 index (the C3/C4 stand-in), BM25 index")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "numpy", "rank-bm25", "sentence-transformers", "torch", "transformers")})
pdf_bytes = open(PDF, "rb").read()
print("pdf sha256", hashlib.sha256(pdf_bytes).hexdigest())
pages = [p.get_text() for p in pymupdf.open(PDF)]
md06 = (WS / "06_RAG_PROJECT_AND_EVALUATION_PLAN.md").read_text(encoding="utf-8")
md07 = (WS / "07_SAMPLE_LESSON.md").read_text(encoding="utf-8")
cc.RECIPE_06 = cc.code_blocks(cc.section(md06, "5.3 Corpus freezing"), "python")[0]
parser = {**cc.PARSER, "version": pymupdf.VersionBind}
manifest06 = cc.build_manifest("climate", pages, pdf_bytes, parser, cc.CLEANING_NONE)
SNAP = manifest06["snapshot_id"]
doc_text = "\n".join(pages)
starts = [r["doc_char_start"] for r in manifest06["docs"][0]["page_table"]]
print(f"pages={len(pages)} doc chars={len(doc_text)} snapshot_id={SNAP} (expected ea07572562ac: {SNAP == 'ea07572562ac'})")
core, chunking, _ = cc.load_07_modules(md07)
cfg = chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page")
dch = chunking.chunk_document("climate", SNAP, pages, cfg)
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
PH = hashlib.sha256(json.dumps(CHUNKING, sort_keys=True).encode("utf-8")).hexdigest()[:12]
chunks = [{"doc_id": "climate", "snapshot_id": SNAP, "chunk_id": f"climate:{SNAP}:{PH}:{c.seq:05d}", "seq": c.seq,
           "char_start": c.char_start, "char_end": c.char_end,
           "page_segments": [{"page": g.page, "char_start": g.char_start, "char_end": g.char_end} for g in c.page_segments],
           "text": c.text, "text_sha256": c.text_sha256, "chunker": CHUNKING["name"], "params_hash": PH, "meta": {}}
          for c in dch]
_jl = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")
SHA_JL = hashlib.sha256(_jl).hexdigest()
print(f"chunks={len(chunks)} params_hash={PH} chunks.jsonl sha256 {SHA_JL} (= C2/C3/C4 d4108b89...: "
      f"{SHA_JL == 'd4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b'})")
IDS = [c["chunk_id"] for c in chunks]
print("chunk_id string order == row order:", IDS == sorted(IDS))
ROW = {d: i for i, d in enumerate(IDS)}
PAGE = {c["chunk_id"]: c["page_segments"][0]["page"] for c in chunks}
SEQ = {c["chunk_id"]: c["seq"] for c in chunks}

from sentence_transformers import SentenceTransformer  # noqa: E402

model = SentenceTransformer(MINILM, device="cpu")


def embed(texts):
    return model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)


V = embed([c["text"] for c in chunks])
print(f"V shape={V.shape} dtype={V.dtype}")
BM_NORM = BM25Okapi([tok_norm(c["text"]) for c in chunks])
BM_SPLIT = BM25Okapi([tok_split(c["text"]) for c in chunks])
print(f"BM25Okapi(k1={BM_NORM.k1}, b={BM_NORM.b}, epsilon={BM_NORM.epsilon}) over tok_norm: avgdl={BM_NORM.avgdl:.2f} "
      f"vocab={len(BM_NORM.idf)}; over split(): avgdl={BM_SPLIT.avgdl:.2f} vocab={len(BM_SPLIT.idf)}")


def dense_scores(q):
    qv = embed([q])[0]
    s = V @ qv
    return {IDS[i]: float(s[i]) for i in range(len(IDS))}


def bm25_scores(q, bm=BM_NORM, tok=tok_norm):
    s = bm.get_scores(tok(q))
    return {IDS[i]: float(s[i]) for i in range(len(IDS))}


# seeds (06 §6.7 machine-readable block), gold segments -> document offsets
seed_block = cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0]
SEEDS = [json.loads(line) for line in seed_block.splitlines() if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
TEXTS = {"climate": doc_text}
print(f"seeds: {len(SEEDS)} ({len(ANS)} answerable)", [(s["qid"], s["category"]) for s in SEEDS])


def rel_id(d, s):
    c = chunks[ROW[d]]
    return cc.rel(("climate", c["char_start"], c["char_end"]), s["G"], TEXTS)


def ce_ids(ids, s):
    return cc.ce(s["G"], [("climate", chunks[ROW[d]]["char_start"], chunks[ROW[d]]["char_end"]) for d in ids], TEXTS)


def first_rel(ranking, s):
    return next((r for r, d in enumerate(ranking, 1) if rel_id(d, s)), None)


def first_ce(ranking, s):
    for r in range(1, len(ranking) + 1):
        if ce_ids(ranking[:r], s):
            return r
    return None


# per-seed raw scores, computed once
DS = {s["qid"]: dense_scores(s["question"]) for s in SEEDS}
BS = {s["qid"]: bm25_scores(s["question"]) for s in SEEDS}
BSS = {s["qid"]: bm25_scores(s["question"], BM_SPLIT, tok_split) for s in SEEDS}


def arms_for(qid, k_rrf=K_RRF, n=N_LIST, alpha=0.5):
    """All rankings for one seed. Each value: list of chunk_ids, best first."""
    d, b = DS[qid], BS[qid]
    dl, bl = top_list(d, n), top_list(b, n, positive_only=True)
    out = {
        "dense": order(d),
        "bm25": order(top_list(b, len(IDS), positive_only=True)),
        "bm25_split": order(top_list(BSS[qid], len(IDS), positive_only=True)),
        "rrf60": order(rrf([order(dl), order(bl)], k_rrf)),
        "mm_0.5": order(weighted({"dense": dl, "bm25": bl}, {"dense": alpha, "bm25": 1 - alpha}, minmax)),
        "mm_0.6": order(weighted({"dense": dl, "bm25": bl}, {"dense": 0.6, "bm25": 0.4}, minmax)),
        "z3_0.6": order(weighted({"dense": dl, "bm25": bl}, {"dense": 0.6, "bm25": 0.4}, zscore3)),
    }
    return out


ARMS = ["dense", "bm25", "bm25_split", "rrf60", "mm_0.5", "mm_0.6", "z3_0.6"]


def summarise(rank_fn, label, seeds=ANS, k=K):
    hit = ce_ = 0
    rr = []
    per = {}
    for s in seeds:
        rk = rank_fn(s["qid"])
        fr = first_rel(rk, s)
        hit += int(fr is not None and fr <= k)
        ce_ += ce_ids(rk[:k], s)
        rr.append(1.0 / fr if (fr is not None and fr <= 10) else 0.0)
        per[s["qid"]] = fr
    return {"label": label, "hit": hit, "ce": ce_, "mrr10": sum(rr) / len(rr), "first_rel": per}


# ================================================================ S2 toy: RRF by hand on the O1-Q09 rankings
head("S2 TOY: RRF by hand on the O1-Q09 rankings (dense [A,B,C], BM25 [C,A,D])")
DENSE_T, BM25_T = ["A", "B", "C"], ["C", "A", "D"]
for kk in (60, 0, 1, 120):
    f = rrf([DENSE_T, BM25_T], kk)
    exact = {d: sum(Fraction(1, kk + r) for lst in (DENSE_T, BM25_T) for r, x in enumerate(lst, 1) if x == d) for d in f}
    print(f"  k={kk:3d}: " + ", ".join(f"{d}={f[d]:.6f} ({exact[d]})" for d in order(f)) + f"  -> order {order(f)}")
f60 = rrf([DENSE_T, BM25_T], 60)
print(f"  gap A - C at k=60 = {f60['A'] - f60['C']:.6f}; gap C - B = {f60['C'] - f60['B']:.6f}; B - D = {f60['B'] - f60['D']:.6f}")
emit("toy_rrf_order_k60", order(f60))
emit("toy_rrf_scores_k60_r5", {d: round(v, 5) for d, v in f60.items()})
# The AIQ challenge-17 lists (external review §5): k decides the winner.
L1, L2 = [0, 1, 2, 3, 4], [4, 1, 3, 2, 0]
for kk in (60, 0):
    f = rrf([L1, L2], kk)
    print(f"  AIQ lists {L1} + {L2}, k={kk}: order {order(f)}; scores " + ", ".join(f"{d}:{f[d]:.5f}" for d in order(f)))
emit("aiq_order_k60", order(rrf([L1, L2], 60)))
emit("aiq_order_k0", order(rrf([L1, L2], 0)))
# the consensus bound: a single-list rank-1 vs a doc ranked n-th in both lists
print(f"  single list, rank 1: 1/61 = {1 / 61:.6f}; both lists at rank 50: 2/110 = {2 / 110:.6f}; "
      f"both at rank 61: 2/121 = {2 / 121:.6f}; both at rank 62: 2/122 = {2 / 122:.6f}")
print(f"  rank-1 vs rank-50 contribution: 1/61 = {1 / 61:.4f}, 1/110 = {1 / 110:.4f}, ratio {(1 / 61) / (1 / 110):.3f}; "
      f"k=0: 1/1 vs 1/50, ratio {1 / (1 / 50):.1f}")

# ================================================================ S3 toy: normalisation and weighted fusion by hand
head("S3 TOY: the same lists with made-up scores; min-max, mean +/- 3 sd, weighted sums")
DENSE_TS = {"A": 0.62, "B": 0.58, "C": 0.41}                 # toy cosine scores (made up)
BM25_TS = {"C": 7.9, "A": 2.1, "D": 1.8}                     # toy BM25 scores (made up)
mmD, mmB = minmax(DENSE_TS), minmax(BM25_TS)
print("  min-max dense:", {d: round(v, 4) for d, v in mmD.items()}, "| min-max BM25:", {d: round(v, 4) for d, v in mmB.items()})
for wd in (0.5, 0.6, 0.7, 0.3):
    f = weighted({"dense": DENSE_TS, "bm25": BM25_TS}, {"dense": wd, "bm25": 1 - wd}, minmax)
    print(f"  min-max weighted dense {wd}/bm25 {1 - wd:.1f}: " + ", ".join(f"{d}={f[d]:.4f}" for d in order(f))
          + f" -> {order(f)}")
f55 = weighted({"dense": DENSE_TS, "bm25": BM25_TS}, {"dense": 0.5, "bm25": 0.5}, minmax)
f64 = weighted({"dense": DENSE_TS, "bm25": BM25_TS}, {"dense": 0.6, "bm25": 0.4}, minmax)
emit("toy_mm55_order", order(f55))
emit("toy_mm64_order", order(f64))
emit("toy_mm64_scores_r4", {d: round(v, 4) for d, v in f64.items()})
zD, zB = zscore3(DENSE_TS), zscore3(BM25_TS)
print("  +/-3sd dense:", {d: round(v, 4) for d, v in zD.items()}, "| +/-3sd BM25:", {d: round(v, 4) for d, v in zB.items()})
fz = weighted({"dense": DENSE_TS, "bm25": BM25_TS}, {"dense": 0.6, "bm25": 0.4}, zscore3)
print("  +/-3sd weighted 0.6/0.4: " + ", ".join(f"{d}={fz[d]:.4f}" for d in order(fz)) + f" -> {order(fz)}")
emit("toy_z64_order", order(fz))
raw = {d: DENSE_TS.get(d, 0) + BM25_TS.get(d, 0) for d in set(DENSE_TS) | set(BM25_TS)}
print("  raw sum (no normalisation): " + ", ".join(f"{d}={raw[d]:.2f}" for d in order(raw)) + f" -> {order(raw)}")
# rescaling one list
for name, tr in (("BM25 x10", lambda x: x * 10), ("BM25 sqrt", math.sqrt)):
    b2 = {d: tr(v) for d, v in BM25_TS.items()}
    r_raw = {d: DENSE_TS.get(d, 0) + b2.get(d, 0) for d in set(DENSE_TS) | set(b2)}
    r_mm = weighted({"dense": DENSE_TS, "bm25": b2}, {"dense": 0.6, "bm25": 0.4}, minmax)
    r_rrf = rrf([order(DENSE_TS), order(b2)])
    print(f"  after {name}: raw-sum order {order(r_raw)}; min-max 0.6/0.4 order {order(r_mm)} "
          f"(A={r_mm['A']:.4f}); RRF order {order(r_rrf)}")
# Dense transformed by a monotone non-linear map (exp(10 s)): min-max order can change, RRF cannot.
dexp = {d: math.exp(10 * v) for d, v in DENSE_TS.items()}
r_mm = weighted({"dense": dexp, "bm25": BM25_TS}, {"dense": 0.6, "bm25": 0.4}, minmax)
print(f"  dense -> exp(10 s): min-max(dense) {({d: round(v, 4) for d, v in minmax(dexp).items()})}; "
      f"min-max 0.6/0.4 order {order(r_mm)} (B={r_mm['B']:.4f}, C={r_mm['C']:.4f}); RRF order {order(rrf([order(dexp), BM25_T]))}")
emit("toy_exp_mm64_order", order(r_mm))
# Normalisation of small toy lists
for lst in ([2, 4, 6], [1, 2, 3, 4, 100], [0.46, 0.45]):
    s = {f"x{i}": v for i, v in enumerate(lst)}
    print(f"  list {lst}: min-max {[round(v, 4) for v in minmax(s).values()]}; +/-3sd (population sd) "
          f"{[round(v, 4) for v in zscore3(s).values()]}; +/-3sd (sample sd) {[round(v, 4) for v in zscore3(s, ddof=1).values()]}")
emit("toy_246_mm", [round(v, 3) for v in minmax({"a": 2, "b": 4, "c": 6}).values()])
emit("toy_246_z3", [round(v, 3) for v in zscore3({"a": 2, "b": 4, "c": 6}).values()])
# max |z| for n points (population sd) = (n-1)/sqrt(n): when can a value leave [0, 1]?
for n in (2, 5, 10, 11, 50, 97):
    print(f"  n={n:3d}: largest possible |z| with population sd = (n-1)/sqrt(n) = {(n - 1) / math.sqrt(n):.3f}")

# ================================================================ S4 the 10 seeds: dense, BM25, fused
head("S4 the 10 draft seeds (draft-seed observations): first relevant rank per arm; Hit@4, CE@4, MRR@10")
rows = {s["qid"]: arms_for(s["qid"]) for s in SEEDS}
print("  qid    category              " + " ".join(f"{a:>10s}" for a in ARMS))
for s in ANS:
    print(f"  {s['qid']}  {s['category']:20s} " + " ".join(f"{str(first_rel(rows[s['qid']][a], s)):>10s}" for a in ARMS))
SUMM = {}
for a in ARMS:
    sm = summarise(lambda q, a=a: rows[q][a], a)
    SUMM[a] = sm
    print(f"  {a:10s}: Hit@4 {sm['hit']}/8  CE@4 {sm['ce']}/8  MRR@10 {sm['mrr10']:.3f}")
print("  first CE rank per arm:")
for s in ANS:
    print(f"    {s['qid']}: " + ", ".join(f"{a}={first_ce(rows[s['qid']][a], s)}" for a in ARMS))
emit("seeds_first_rel_dense", SUMM["dense"]["first_rel"])
emit("seeds_first_rel_bm25", SUMM["bm25"]["first_rel"])
emit("seeds_first_rel_rrf60", SUMM["rrf60"]["first_rel"])
emit("seeds_first_rel_mm05", SUMM["mm_0.5"]["first_rel"])
emit("seeds_first_rel_z306", SUMM["z3_0.6"]["first_rel"])
emit("seeds_hit_ce", {a: [SUMM[a]["hit"], SUMM[a]["ce"]] for a in ("dense", "bm25", "rrf60", "mm_0.5", "z3_0.6")})
print("  helps / hurts vs dense (first relevant rank):")
for a in ("bm25", "rrf60", "mm_0.5", "mm_0.6", "z3_0.6"):
    better = [s["qid"] for s in ANS if (SUMM[a]["first_rel"][s["qid"]] or 99) < (SUMM["dense"]["first_rel"][s["qid"]] or 99)]
    worse = [s["qid"] for s in ANS if (SUMM[a]["first_rel"][s["qid"]] or 99) > (SUMM["dense"]["first_rel"][s["qid"]] or 99)]
    print(f"    {a:8s}: better {better}; worse {worse}")
print("  top-4 of each arm for every seed (seq numbers; * = relevant):")
for s in SEEDS:
    line = []
    for a in ("dense", "bm25", "rrf60", "mm_0.5"):
        t4 = rows[s["qid"]][a][:K]
        line.append(f"{a}=[" + ",".join(f"{SEQ[d]}{'*' if (s['answerable'] and rel_id(d, s)) else ''}" for d in t4) + "]")
    print(f"    {s['qid']}: " + " ".join(line))
print("  overlap of the dense and BM25 top-4 (the Venn diagram, Ch12 p.7/14):")
for s in SEEDS:
    a4, b4 = set(rows[s["qid"]]["dense"][:K]), set(rows[s["qid"]]["bm25"][:K])
    print(f"    {s['qid']}: both {len(a4 & b4)}, dense only {len(a4 - b4)}, BM25 only {len(b4 - a4)}")
both = [len(set(rows[s["qid"]]["dense"][:K]) & set(rows[s["qid"]]["bm25"][:K])) for s in SEEDS]
print(f"  shared top-4 chunks over 10 seeds: {both}; total {sum(both)} of 40")
emit("seeds_top4_overlap", both)
print("  BM25 list lengths (score > 0): " + ", ".join(f"{s['qid']}={len(top_list(BS[s['qid']], 999, True))}" for s in SEEDS))
print("  query tokens (tok_norm): " + "; ".join(f"{s['qid']}={tok_norm(s['question'])}" for s in SEEDS[:4]))

# ================================================================ S5 per-seed details for the lesson's walk-through
head("S5 walk-through seeds: D-008 (exact term), D-006 (paraphrase), D-002 (near-duplicate distractor)")
for qid in ("D-008", "D-006", "D-002", "D-004", "D-001"):
    s = next(x for x in SEEDS if x["qid"] == qid)
    d, b = DS[qid], BS[qid]
    dl, bl = top_list(d, N_LIST), top_list(b, N_LIST, True)
    od, ob = order(dl), order(bl)
    fr = rrf([od, ob])
    mmf = weighted({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, minmax)
    print(f"\n  {qid} {s['question']!r} tokens={tok_norm(s['question'])}")
    for name, lst, sc in (("dense", od, dl), ("bm25", ob, bl)):
        print(f"    {name} top-6: " + "; ".join(f"r{r} seq{SEQ[x]} p.{PAGE[x]} {sc[x]:.4f}{' REL' if rel_id(x, s) else ''}"
                                         for r, x in enumerate(lst[:6], 1)))
    for name, f in (("rrf60", fr), ("mm_0.5", mmf)):
        o = order(f)
        print(f"    {name} top-6: " + "; ".join(
            f"r{r} seq{SEQ[x]} {f[x]:.5f} (dense r{od.index(x) + 1 if x in dl else '-'}, bm25 r{ob.index(x) + 1 if x in bl else '-'})"
            f"{' REL' if rel_id(x, s) else ''}" for r, x in enumerate(o[:6], 1)))
    idf = {t: (round(BM_NORM.idf[t], 4) if t in BM_NORM.idf else "OOV") for t in tok_norm(s["question"])}
    print(f"    idf of the query tokens (OOV = not in any chunk, adds 0): {idf}")
    for name, lst in (("dense", od), ("bm25", ob)):
        for x in lst[:2]:
            toks = set(tok_norm(chunks[ROW[x]]["text"]))
            hit = [t for t in dict.fromkeys(tok_norm(s["question"])) if t in toks and t in BM_NORM.idf]
            print(f"      {name} seq{SEQ[x]} p.{PAGE[x]}: query tokens present {hit}; text {chunks[ROW[x]]['text'][:110]!r}")
    print(f"    rank of the dense rank-1 chunk (seq{SEQ[od[0]]}) in rrf60: {order(fr).index(od[0]) + 1}; in mm_0.5: "
          f"{order(mmf).index(od[0]) + 1}; is it in the BM25 top-50: {od[0] in bl}")

# The D-006 RRF tie and the D-002 near tie
f6 = rrf([order(top_list(DS["D-006"], N_LIST)), order(top_list(BS["D-006"], N_LIST, True))])
o6 = order(f6)
print(f"\n  D-006 RRF: r1 seq{SEQ[o6[0]]} {f6[o6[0]]!r} and r2 seq{SEQ[o6[1]]} {f6[o6[1]]!r}: exactly equal = "
      f"{f6[o6[0]] == f6[o6[1]]} (1/61 + 1/62 both ways); the order is decided by the smaller chunk_id")
f2 = rrf([order(top_list(DS["D-002"], N_LIST)), order(top_list(BS["D-002"], N_LIST, True))])
o2 = order(f2)
print(f"  D-002 RRF: r1 seq{SEQ[o2[0]]} {f2[o2[0]]:.6f} (1/63 + 1/61) vs r2 seq{SEQ[o2[1]]} {f2[o2[1]]:.6f} (2/62): "
      f"margin {f2[o2[0]] - f2[o2[1]]:.6f}")
n_df = {t: sum(t in set(tok_norm(c["text"])) for c in chunks) for t in ("kigali", "amendment", "the", "ipcc", "beccs")}
raw_idf = {t: round(math.log(len(chunks) - n + 0.5) - math.log(n + 0.5), 4) for t, n in n_df.items()}
print(f"  document frequency n over 97 chunks: {n_df}; raw idf ln((N-n+0.5)/(n+0.5)): {raw_idf}; "
      f"epsilon floor 0.25 x mean idf = {BM_NORM.epsilon * BM_NORM.average_idf:.4f}")

# ================================================================ S5b the worked example carried through (D-008)
head("S5b worked example, D-008 'What does the Kigali Amendment target?' (draft seed; real scores)")
qid = "D-008"
s8 = next(x for x in SEEDS if x["qid"] == qid)
dl, bl = top_list(DS[qid], N_LIST), top_list(BS[qid], N_LIST, True)
od, ob = order(dl), order(bl)
mD, mB = minmax(dl), minmax(bl)
zD8, zB8 = zscore3(dl), zscore3(bl)
print(f"  dense list: {len(dl)} chunks, max {max(dl.values()):.4f}, min (50th) {min(dl.values()):.4f}; "
      f"BM25 list: {len(bl)} chunks, max {max(bl.values()):.4f}, min (50th) {min(bl.values()):.4f}")
for x in sorted(set(od[:4]) | set(ob[:4]), key=lambda x: SEQ[x]):
    print(f"  seq{SEQ[x]:2d} p.{PAGE[x]:2d} rel={rel_id(x, s8)}: dense raw {dl.get(x, float('nan')):.4f} "
          f"(r{od.index(x) + 1 if x in dl else '-'}) mm {mD.get(x, 0.0):.4f} z3 {zD8.get(x, float('nan')):.4f} | "
          f"bm25 raw {bl.get(x, float('nan')):.4f} (r{ob.index(x) + 1 if x in bl else '-'}) mm {mB.get(x, 0.0):.4f} "
          f"z3 {zB8.get(x, float('nan')):.4f}")
f8 = rrf([od, ob])
w8 = weighted({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, minmax)
w8b = weighted({"dense": dl, "bm25": bl}, {"dense": 0.6, "bm25": 0.4}, minmax)
z8 = weighted({"dense": dl, "bm25": bl}, {"dense": 0.6, "bm25": 0.4}, zscore3)
raw8 = {x: dl.get(x, 0.0) + bl.get(x, 0.0) for x in set(dl) | set(bl)}
for name, f in (("raw sum", raw8), ("min-max 0.5/0.5", w8), ("min-max 0.6/0.4", w8b), ("+/-3sd 0.6/0.4", z8), ("RRF k=60", f8)):
    o = order(f)
    print(f"  {name:16s} top-4: " + "; ".join(f"seq{SEQ[x]} {f[x]:.5f}{' REL' if rel_id(x, s8) else ''}" for x in o[:4]))
x69 = next(x for x in IDS if SEQ[x] == 69)
print(f"  seq69 RRF = 1/(60+{od.index(x69) + 1}) + 1/(60+{ob.index(x69) + 1}) = {1 / (60 + od.index(x69) + 1):.6f} + "
      f"{1 / (60 + ob.index(x69) + 1):.6f} = {f8[x69]:.6f}")
x28 = next(x for x in IDS if SEQ[x] == 28)
print(f"  seq28 (dense r1, not in the BM25 top-50): RRF = 1/61 = {f8[x28]:.6f}, fused rank {order(f8).index(x28) + 1}; "
      f"min-max 0.5/0.5 = {w8[x28]:.4f}, fused rank {order(w8).index(x28) + 1}")
print(f"  BM25 gap r1-r2 {bl[ob[0]] - bl[ob[1]]:.4f} (ratio {bl[ob[0]] / bl[ob[1]]:.2f}); dense gap r1-r2 {dl[od[0]] - dl[od[1]]:.4f}")
emit("lab_d008_rrf_top4", order(f8)[:K])
emit("lab_d008_mm05_top4", order(w8)[:K])

# ================================================================ S6 exact-term demonstration queries (P3's five)
head("S6 DEMONSTRATION: P3's five exact-term queries on the 97 v0 chunks (target = chunks containing the string)")
DEMO = [("IPCC", "IPCC"), ("What does BECCS stand for?", "BECCS"), ("methane CH4", "CH4"),
        ("Kyoto Protocol 1997", "1997"), ("limit warming to 1.5 degrees", "1.5")]
demo_out = {}
for qtext, target in DEMO:
    tgt = [c["chunk_id"] for c in chunks if target in c["text"]]
    d, b, bsp = dense_scores(qtext), bm25_scores(qtext), bm25_scores(qtext, BM_SPLIT, tok_split)
    dl, bl = top_list(d, N_LIST), top_list(b, N_LIST, True)
    rk = {"dense": order(d), "bm25": order(top_list(b, 999, True)), "bm25_split": order(top_list(bsp, 999, True)),
          "rrf60": order(rrf([order(dl), order(bl)])),
          "mm_0.5": order(weighted({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, minmax))}
    fr = {a: next((r for r, x in enumerate(v, 1) if x in tgt), None) for a, v in rk.items()}
    demo_out[qtext] = fr
    print(f"  {qtext!r}: target {target!r} in seqs {[SEQ[x] for x in tgt]} (pages {sorted({PAGE[x] for x in tgt})}); "
          f"first target rank: " + ", ".join(f"{a}={v}" for a, v in fr.items())
          + f"; BM25(norm) list length {len(rk['bm25'])}, BM25(split) list length {len(rk['bm25_split'])}")
emit("demo_first_target", demo_out)
# The paraphrase variant of D-002 (06 §6.7, example only, not one of the 10 seeds)
s002 = next(x for x in SEEDS if x["qid"] == "D-002")
qv = "When did countries adopt the Paris climate accord?"
d, b = dense_scores(qv), bm25_scores(qv)
dl, bl = top_list(d, N_LIST), top_list(b, N_LIST, True)
pv = {"dense": order(d), "bm25": order(top_list(b, 999, True)), "rrf60": order(rrf([order(dl), order(bl)])),
      "mm_0.5": order(weighted({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, minmax))}
print(f"  paraphrase variant D-002-P1 {qv!r} (06 §6.7 example; D-002 gold): first relevant rank "
      + ", ".join(f"{a}={first_rel(v, s002)}" for a, v in pv.items())
      + f"; CE@4: " + ", ".join(f"{a}={ce_ids(v[:K], s002)}" for a, v in pv.items()))

# ================================================================ S7 RRF's consensus property on the seeds
head("S7 RRF k=60 over two top-50 lists: does every chunk in BOTH lists outrank every chunk in ONE list?")
cons = []
for s in SEEDS:
    dl, bl = top_list(DS[s["qid"]], N_LIST), top_list(BS[s["qid"]], N_LIST, True)
    f = rrf([order(dl), order(bl)])
    in_both = set(dl) & set(bl)
    one = set(f) - in_both
    ok = (min(f[x] for x in in_both) > max(f[x] for x in one)) if (in_both and one) else None
    cons.append(ok)
    print(f"  {s['qid']}: in both lists {len(in_both)}, in one list {len(one)}, union {len(f)}; "
          f"min(both) {min(f[x] for x in in_both):.5f} > max(one) {max(f[x] for x in one):.5f}: {ok}")
print(f"  property holds for {sum(bool(x) for x in cons)}/10 seeds (theory: always, for list depth <= 61 at k=60)")
emit("consensus_in_both", [len(set(top_list(DS[s['qid']], N_LIST)) & set(top_list(BS[s['qid']], N_LIST, True))) for s in SEEDS])

# ================================================================ S8 normalisation behaviour on real lists
head("S8 normalisation on the real top-50 lists: ranges, out-of-range +/-3 sd values, what 1.0 means")
oor = {"dense": 0, "bm25": 0}
tot = {"dense": 0, "bm25": 0}
for s in SEEDS:
    for name, sc in (("dense", top_list(DS[s["qid"]], N_LIST)), ("bm25", top_list(BS[s["qid"]], N_LIST, True))):
        z = zscore3(sc)
        oor[name] += sum(v < 0 or v > 1 for v in z.values())
        tot[name] += len(z)
print(f"  +/-3sd values outside [0, 1] over 10 seeds: dense {oor['dense']}/{tot['dense']}, BM25 {oor['bm25']}/{tot['bm25']}")
for s in SEEDS:
    for name, sc in (("dense", top_list(DS[s["qid"]], N_LIST)), ("bm25", top_list(BS[s["qid"]], N_LIST, True))):
        z = zscore3(sc)
        o = order(sc)
        print(f"    {s['qid']} {name:5s}: raw top {sc[o[0]]:.4f} 2nd {sc[o[1]]:.4f} 50th {sc[o[-1]]:.4f} | min-max top {minmax(sc)[o[0]]:.3f}"
              f" 2nd {minmax(sc)[o[1]]:.3f} | z3 top {z[o[0]]:.3f} 2nd {z[o[1]]:.3f} 50th {z[o[-1]]:.3f}")
print("  unanswerable seeds: the best chunk still normalises to 1.0 (min-max):")
for qid in ("D-009", "D-010"):
    dl, bl = top_list(DS[qid], N_LIST), top_list(BS[qid], N_LIST, True)
    print(f"    {qid}: dense raw top {max(dl.values()):.4f} -> {max(minmax(dl).values()):.1f}; BM25 raw top "
          f"{max(bl.values()):.4f} -> {max(minmax(bl).values()):.1f}")
answ_top = [max(DS[s["qid"]].values()) for s in ANS]
print(f"  answerable dense raw top-1 min/median/max: {min(answ_top):.4f}/{st.median(answ_top):.4f}/{max(answ_top):.4f}")

# ================================================================ S9 rescaling one scorer: which methods change their top-4?
head("S9 rescale ONE scorer: how many of the 10 seeds change their ordered top-4?")


def fused_top4(qid, method, dtr=lambda x: x, btr=lambda x: x):
    dl = {k: dtr(v) for k, v in top_list(DS[qid], N_LIST).items()}
    bl = {k: btr(v) for k, v in top_list(BS[qid], N_LIST, True).items()}
    if method == "raw_sum":
        f = {x: dl.get(x, 0.0) + bl.get(x, 0.0) for x in set(dl) | set(bl)}
    elif method == "mm_0.5":
        f = weighted({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, minmax)
    elif method == "z3_0.5":
        f = weighted({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, zscore3)
    else:
        f = rrf([order(dl), order(bl)])
    return order(f)[:K]


TRANS = [("dense x100", lambda x: 100 * x, lambda x: x), ("BM25 x10", lambda x: x, lambda x: 10 * x),
         ("dense exp(10s)", lambda x: math.exp(10 * x), lambda x: x), ("BM25 sqrt", lambda x: x, math.sqrt)]
chg = {}
for m in ("raw_sum", "mm_0.5", "z3_0.5", "rrf60"):
    base = {s["qid"]: fused_top4(s["qid"], m) for s in SEEDS}
    for tname, dtr, btr in TRANS:
        n = sum(fused_top4(s["qid"], m, dtr, btr) != base[s["qid"]] for s in SEEDS)
        chg[f"{m}|{tname}"] = n
    print(f"  {m:8s}: " + ", ".join(f"{t[0]} -> {chg[f'{m}|{t[0]}']}/10" for t in TRANS))
emit("rescale_changes", chg)
rawsum_ce = sum(ce_ids(fused_top4(s["qid"], "raw_sum"), s) for s in ANS)
print(f"  raw sum (no normalisation), CE@4 {rawsum_ce}/8; overlap of raw-sum top-4 with BM25 top-4: "
      f"{sum(len(set(fused_top4(s['qid'], 'raw_sum')) & set(rows[s['qid']]['bm25'][:K])) for s in SEEDS)}/40")

# ================================================================ S10 CR-08 probes: k_rrf and the weight
head("S10 CR-08 probes on the seeds: change k_rrf; change the dense weight (min-max, top-50)")
base60 = {s["qid"]: rows[s["qid"]]["rrf60"][:K] for s in SEEDS}
kr = {}
for kk in (0, 1, 10, 60, 120, 1000):
    sm = summarise(lambda q, kk=kk: arms_for(q, k_rrf=kk)["rrf60"], f"rrf k={kk}")
    nchg = sum(arms_for(s["qid"], k_rrf=kk)["rrf60"][:K] != base60[s["qid"]] for s in SEEDS)
    kr[kk] = [sm["hit"], sm["ce"], nchg]
    print(f"  k_rrf={kk:4d}: Hit@4 {sm['hit']}/8 CE@4 {sm['ce']}/8 MRR@10 {sm['mrr10']:.3f}; seeds whose top-4 differs from k=60: {nchg}/10")
emit("krrf_sweep", {str(k): v for k, v in kr.items()})
al = {}
for a in (0.0, 0.3, 0.5, 0.6, 0.7, 1.0):
    sm = summarise(lambda q, a=a: arms_for(q, alpha=a)["mm_0.5"], f"mm a={a}")
    al[a] = [sm["hit"], sm["ce"]]
    print(f"  dense weight {a:.1f} / BM25 {1 - a:.1f}: Hit@4 {sm['hit']}/8 CE@4 {sm['ce']}/8 MRR@10 {sm['mrr10']:.3f} "
          f"first_rel {sm['first_rel']}")
emit("alpha_sweep", {str(k): v for k, v in al.items()})
id1 = all(arms_for(s["qid"], alpha=1.0)["mm_0.5"][:K] == rows[s["qid"]]["dense"][:K] for s in SEEDS)
id0 = all(arms_for(s["qid"], alpha=0.0)["mm_0.5"][:K] == rows[s["qid"]]["bm25"][:K] for s in SEEDS)
print(f"  identity test: weight 1.0 top-4 == dense top-4 for all 10 seeds: {id1}; weight 0.0 top-4 == BM25 top-4: {id0}")

# ================================================================ S11 the repo bug, replicated with MiniLM
head("S11 the repo's fusion (cell 17 / runnable script L75-L86) replicated on our chunks with MiniLM")
e0 = embed([""])[0]
dist0 = ((V - e0) ** 2).sum(axis=1)                          # squared L2, as a FAISS IndexFlatL2 search returns
ALL_DOCS = sorted(range(len(IDS)), key=lambda i: (float(dist0[i]), i))   # L75: similarity_search("", k=ntotal)


def repo_fusion(query, k=5, alpha=0.5, eps=1e-8, bm=BM_SPLIT, tok=tok_split):
    """A transcription of the repo logic with numpy arrays. Returns ROW indices into chunks."""
    bm25_s = bm.get_scores(tok(query))                         # L76: corpus (index) order
    qv = embed([query])[0]
    dq = ((V - qv) ** 2).sum(axis=1)
    vr = sorted(range(len(IDS)), key=lambda i: (float(dq[i]), i))   # L77: nearest first
    vs = np.array([dq[i] for i in vr])                          # L79
    vs = 1 - (vs - vs.min()) / (vs.max() - vs.min() + eps)      # L80 (cell 17 adds eps)
    bm25_s = (bm25_s - bm25_s.min()) / (bm25_s.max() - bm25_s.min() + eps)   # L81
    comb = alpha * vs + (1 - alpha) * bm25_s                    # L83: element i mixes three different documents
    idx = np.argsort(comb)[::-1]                                # L84
    return [ALL_DOCS[i] for i in idx[:k]], vs, vr               # L86


def aligned_fusion(query, k=5, alpha=0.5, eps=1e-8, bm=BM_SPLIT, tok=tok_split):
    """The same formula with every array indexed by the SAME chunk row."""
    bm25_s = bm.get_scores(tok(query))
    qv = embed([query])[0]
    dq = ((V - qv) ** 2).sum(axis=1)
    vs = 1 - (dq - dq.min()) / (dq.max() - dq.min() + eps)
    bm25_s = (bm25_s - bm25_s.min()) / (bm25_s.max() - bm25_s.min() + eps)
    comb = alpha * vs + (1 - alpha) * bm25_s
    return sorted(range(len(IDS)), key=lambda i: (-float(comb[i]), IDS[i]))[:k]


Q19 = "What are the impacts of climate change on the environment?"   # fusion_retrieval.ipynb cell 19
bug, vs, vr = repo_fusion(Q19)
ok = aligned_fusion(Q19)
print(f"  ALL_DOCS (order by distance to the empty string) first 5 rows: {ALL_DOCS[:5]}; vector order first 5 rows: {vr[:5]}")
print(f"  normalised vector array is a ramp, non-increasing by position: {bool(np.all(np.diff(vs) <= 1e-12))}; "
      f"first {vs[0]:.3f}, last {vs[-1]:.3f}")
print(f"  cell-19 query, k=5, alpha=0.5: repo-style rows {bug} (seqs {[chunks[i]['seq'] for i in bug]}); "
      f"aligned rows {ok}; overlap {len(set(bug) & set(ok))}/5")
same_a1 = len({tuple(repo_fusion(s['question'], alpha=1.0)[0]) for s in SEEDS})
print(f"  alpha=1.0 (vector only): distinct repo-style top-5 lists over the 10 seeds = {same_a1} "
      f"(the list is {repo_fusion(SEEDS[0]['question'], alpha=1.0)[0]} = ALL_DOCS[:5] for every query)")
dense_top5 = [order(DS[s["qid"]])[:5] for s in SEEDS]
print("  alpha=1.0 repo-style == dense top-5 for any seed:",
      any([IDS[i] for i in repo_fusion(s["question"], alpha=1.0)[0]] == dense_top5[j] for j, s in enumerate(SEEDS)))
hb = cb = ha = ca = 0
ovl = []
for s in ANS:
    b5 = [IDS[i] for i in repo_fusion(s["question"])[0]][:K]
    a5 = [IDS[i] for i in aligned_fusion(s["question"])][:K]
    hb += int(any(rel_id(x, s) for x in b5)); cb += ce_ids(b5, s)
    ha += int(any(rel_id(x, s) for x in a5)); ca += ce_ids(a5, s)
    ovl.append(len(set(b5) & set(a5)))
print(f"  8 answerable seeds, top-4, alpha=0.5, split() BM25 (as the repo): repo-style Hit@4 {hb}/8 CE@4 {cb}/8; "
      f"aligned Hit@4 {ha}/8 CE@4 {ca}/8; overlap per seed {ovl}")
emit("repo_bug_seeds", [hb, cb, ha, ca])
hb2 = cb2 = 0
for s in ANS:
    b5 = [IDS[i] for i in repo_fusion(s["question"], bm=BM_NORM, tok=tok_norm)[0]][:K]
    hb2 += int(any(rel_id(x, s) for x in b5)); cb2 += ce_ids(b5, s)
print(f"  repo-style with tok_norm BM25 instead (tokenizer fixed, alignment not): Hit@4 {hb2}/8 CE@4 {cb2}/8")
# without epsilon (runnable script L80-L81) on an all-zero BM25 query
with np.errstate(invalid="ignore", divide="ignore"):
    z0 = BM_SPLIT.get_scores(tok_split("IPCC"))
    nn = (z0 - z0.min()) / (z0.max() - z0.min())
print(f"  'IPCC' under split(): all BM25 zero {bool((z0 == 0).all())}; L81 without epsilon -> NaN count {int(np.isnan(nn).sum())}/{len(nn)}")
ip_bug = repo_fusion("IPCC")[0]
ip_dense = [ROW[d] for d in order(dense_scores("IPCC"))[:5]]
print(f"  'IPCC' through the repo-style fusion (cell 17, with epsilon): rows {ip_bug}; == ALL_DOCS[:5] (nearest to the "
      f"empty string) {ip_bug == ALL_DOCS[:5]}; dense top-5 rows {ip_dense}; == dense top-5 {ip_bug == ip_dense}; "
      f"contains the IPCC chunk (seq 1) {1 in ip_bug}")
ip_al = aligned_fusion("IPCC")
print(f"  'IPCC' through the aligned formula: rows {ip_al}; == dense top-5 {ip_al == ip_dense} (all-zero BM25 leaves the vector half)")

# The 3-document toy reproduction (lesson D.6 / lab Task 4)
TOY_DOCS = ["d0", "d1", "d2"]                       # corpus (index) order
TOY_EMPTY_ORDER = [2, 0, 1]                         # rows nearest to the empty string first
TOY_QUERY_ORDER = [1, 2, 0]                         # rows nearest to the query first
TOY_DIST = {1: 0.20, 2: 0.50, 0: 0.90}              # query distances by row (lower = closer)
TOY_BM25 = [3.0, 0.0, 1.0]                          # BM25 by row (corpus order)
vs_t = np.array([TOY_DIST[i] for i in TOY_QUERY_ORDER])
vs_t = 1 - (vs_t - vs_t.min()) / (vs_t.max() - vs_t.min())
bm_t = np.array(TOY_BM25)
bm_t = (bm_t - bm_t.min()) / (bm_t.max() - bm_t.min())
comb_t = 0.5 * vs_t + 0.5 * bm_t
buggy_t = [TOY_DOCS[TOY_EMPTY_ORDER[i]] for i in np.argsort(comb_t)[::-1]]
dn = {i: 1 - (TOY_DIST[i] - 0.20) / (0.90 - 0.20) for i in range(3)}
right_t = {TOY_DOCS[i]: 0.5 * dn[i] + 0.5 * float(bm_t[i]) for i in range(3)}
print(f"  TOY 3 docs: vector array by position {np.round(vs_t, 4).tolist()}, BM25 array by row {np.round(bm_t, 4).tolist()}, "
      f"combined by position {np.round(comb_t, 4).tolist()}; repo-style order {buggy_t}; aligned scores "
      f"{ {d: round(v, 4) for d, v in right_t.items()} } -> order {order(right_t)}")
emit("toy_bug_order", buggy_t)
emit("toy_aligned_order", order(right_t))

# ================================================================ S12 tokenizer inside the hybrid (P3 link)
head("S12 the BM25 tokenizer inside the hybrid: split() vs tok_norm (RRF k=60, top-50)")
for name, bsrc in (("split", BSS), ("norm", BS)):
    sm = summarise(lambda q, bsrc=bsrc: order(rrf([order(top_list(DS[q], N_LIST)), order(top_list(bsrc[q], N_LIST, True))])),
                   name)
    print(f"  BM25 tokenizer {name:5s}: hybrid Hit@4 {sm['hit']}/8 CE@4 {sm['ce']}/8 MRR@10 {sm['mrr10']:.3f} first_rel {sm['first_rel']}")

# ================================================================ S13 the LlamaIndex variant's normalisation on 2 candidates
head("S13 llamaindex cells 15/17 keep top-2 per retriever; the cell-20 mean +/- 3 sd formula on two scores")
for a, b in ((0.46, 0.45), (0.9, 0.1), (14.2, 3.1)):
    zp, zs = zscore3({"a": a, "b": b}), zscore3({"a": a, "b": b}, ddof=1)
    print(f"  scores ({a}, {b}): population sd -> ({zp['a']:.4f}, {zp['b']:.4f}); sample sd -> ({zs['a']:.4f}, {zs['b']:.4f})")

# ================================================================ S13b list depth: how many candidates each retriever passes on
head("S13b list depth n per retriever (RRF k=60 and min-max 0.5/0.5): draft seeds, k=4")
for n in (2, 4, 10, 20, 50, 97):
    r_sm = summarise(lambda q, n=n: arms_for(q, n=n)["rrf60"], f"rrf n={n}")
    m_sm = summarise(lambda q, n=n: arms_for(q, n=n)["mm_0.5"], f"mm n={n}")
    viol = 0
    for s in SEEDS:
        dl, bl = top_list(DS[s["qid"]], n), top_list(BS[s["qid"]], n, True)
        f = rrf([order(dl), order(bl)])
        both, one = set(dl) & set(bl), set(f) - (set(dl) & set(bl))
        viol += int(bool(both and one) and min(f[x] for x in both) <= max(f[x] for x in one))
    print(f"  n={n:3d}: RRF Hit@4 {r_sm['hit']}/8 CE@4 {r_sm['ce']}/8 MRR@10 {r_sm['mrr10']:.3f} | min-max Hit@4 {m_sm['hit']}/8 "
          f"CE@4 {m_sm['ce']}/8 MRR@10 {m_sm['mrr10']:.3f} | seeds where a one-list chunk ties or beats a both-list chunk: {viol}/10")

# ================================================================ S14 lab-only fingerprints
head("S14 lab fingerprints (CHECK cells)")
d002 = next(x for x in SEEDS if x["qid"] == "D-002")
dl, bl = top_list(DS["D-002"], N_LIST), top_list(BS["D-002"], N_LIST, True)
emit("lab_d002_dense_top4", order(dl)[:K])
emit("lab_d002_bm25_top4", order(bl)[:K])
emit("lab_d002_rrf_top4", order(rrf([order(dl), order(bl)]))[:K])
emit("lab_d002_mm05_top4", order(weighted({"dense": dl, "bm25": bl}, {"dense": 0.5, "bm25": 0.5}, minmax))[:K])
emit("lab_bm25_len", {s["qid"]: len(top_list(BS[s["qid"]], N_LIST, True)) for s in SEEDS})
emit("lab_hit_ce4", {a: [SUMM[a]["hit"], SUMM[a]["ce"]] for a in ("dense", "bm25", "rrf60", "mm_0.5")})
f6 = rrf([order(top_list(DS["D-006"], N_LIST)), order(top_list(BS["D-006"], N_LIST, True))])
emit("lab_d006_rrf_top2_r6", [round(f6[x], 6) for x in order(f6)[:2]])
n_k0 = sum(arms_for(s["qid"], k_rrf=0)["rrf60"][:K] != rows[s["qid"]]["rrf60"][:K] for s in SEEDS)
n_w07 = sum(arms_for(s["qid"], alpha=0.7)["mm_0.5"][:K] != rows[s["qid"]]["mm_0.5"][:K] for s in SEEDS)
print(f"  CR-08: seeds whose ordered top-4 changes: k_rrf 60 -> 0: {n_k0}/10; dense weight 0.5 -> 0.7 (min-max): {n_w07}/10")
emit("lab_cr08", {"k0": n_k0, "w07": n_w07})
emit("lab_rescale", {"raw_sum|x100": chg["raw_sum|dense x100"], "raw_sum|exp": chg["raw_sum|dense exp(10s)"],
                     "mm|x100": chg["mm_0.5|dense x100"], "mm|exp": chg["mm_0.5|dense exp(10s)"],
                     "rrf|x100": chg["rrf60|dense x100"], "rrf|exp": chg["rrf60|dense exp(10s)"]})
print("DONE")
