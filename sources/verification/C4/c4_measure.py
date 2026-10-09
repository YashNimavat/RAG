"""C4 (dense retrieval) measurements: every measured number in concepts/C4_dense_retrieval.md comes from this run.

Local only: no Groq or Cohere call, no .env read. MiniLM models load from the local Hugging Face cache (offline).
The v0 index is rebuilt here exactly as C3 specifies it (06 §3.1): PyMuPDF 1.26.7 page.get_text(), pages joined
with "\\n", the 07 H.1/H.3 recursive chunker (executed from 07, as the acceptance suite does), per_page, 1000/200,
MiniLM all-MiniLM-L6-v2, normalised, float32. Gold labels: the 10 draft seeds of 06 §6.7 (llm-draft, demo only).
Relevance and CE use the acceptance suite's reference functions (06 §7.2), imported from corrections/contracts_check.py.

Run from rag_learning/ (Git Bash):
    B="C:/Yash/New-Work/Book RAG"
    PYTHONIOENCODING=utf-8 uv run python sources/verification/C4/c4_measure.py \
        "$B/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" \
        > sources/verification/C4/out_c4_measure.txt 2> sources/verification/C4/out_c4_measure.stderr.txt
Sections S1..S9 are deterministic (two runs are diffed in C4_FACTS.md).
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import dataclasses
import hashlib
import importlib.metadata as md
import json
import statistics as st
import sys
import tempfile
from pathlib import Path

import numpy as np
import pymupdf

PDF = sys.argv[1]
WS = Path(__file__).resolve().parents[3]                      # rag_learning/
sys.path.insert(0, str(WS / "sources" / "verification" / "corrections"))
import contracts_check as cc                                  # noqa: E402  (reference rel / ce / 07 loader)

MINILM = "sentence-transformers/all-MiniLM-L6-v2"
OTHER = "sentence-transformers/paraphrase-MiniLM-L3-v2"       # also 384-d: the "wrong query model" demo
K = 4
KS = (1, 2, 4, 8)


def head(t):
    print(f"\n=== {t}")


def fp(x):                                                    # same fingerprint as the lab's _fp
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- the function the lesson teaches
def retrieve(q, V, chunks, k=K):
    """Exact cosine top-k with scores. q: (d,) unit; V: (N, d) unit rows; chunks[i] belongs to row i.
    Ties: smaller chunk_id first (06 §3.1). Returns rank-ordered dicts (the C4 -> C5 interface)."""
    scores = V @ q
    n = len(scores)
    k = min(k, n)
    cand = np.argpartition(-scores, k - 1)[:k]
    kth = scores[cand].min()
    cand = np.flatnonzero(scores >= kth)                      # every row tied with the k-th score
    cand = sorted(cand.tolist(), key=lambda i: (-float(scores[i]), chunks[i]["chunk_id"]))[:k]
    return [{"rank": r, "chunk_id": chunks[i]["chunk_id"], "doc_id": chunks[i]["doc_id"],
             "page": chunks[i]["page_segments"][0]["page"], "char_start": chunks[i]["char_start"],
             "char_end": chunks[i]["char_end"], "score": float(scores[i]), "text": chunks[i]["text"]}
            for r, i in enumerate(cand, 1)]


def full_order(scores, chunks):
    return sorted(range(len(scores)), key=lambda i: (-float(scores[i]), chunks[i]["chunk_id"]))


# ---------------------------------------------------------------- S1
head("S1 environment, snapshot, v0 index (the C3 stand-in)")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "numpy", "sentence-transformers", "torch", "transformers", "tiktoken")})
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
print(f"pages={len(pages)} doc chars={len(doc_text)} snapshot_id={SNAP} (06 §5.3 states ea07572562ac: "
      f"{SNAP == 'ea07572562ac'})")
core, chunking, _ = cc.load_07_modules(md07)
cfg = chunking.ChunkerConfig(name="recursive", size=1000, overlap=200, scope="per_page")
dch = chunking.chunk_document("climate", SNAP, pages, cfg)     # spans from 07 H.1/H.3 (= C2 lab spans)
# Course-wide id decision (coordinator, 2026-10-08; = C2 lab Task 7): params_hash over 06 §2.4's `chunking:` block.
CHUNKING = {"name": "recursive_char", "unit": "chars", "chunk_size": 1000, "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""], "scope": "per_page"}
PH = hashlib.sha256(json.dumps(CHUNKING, sort_keys=True).encode("utf-8")).hexdigest()[:12]
chunks = [{"doc_id": "climate", "snapshot_id": SNAP, "chunk_id": f"climate:{SNAP}:{PH}:{c.seq:05d}", "seq": c.seq,
           "char_start": c.char_start, "char_end": c.char_end,
           "page_segments": [{"page": g.page, "char_start": g.char_start, "char_end": g.char_end} for g in c.page_segments],
           "text": c.text, "text_sha256": c.text_sha256, "chunker": CHUNKING["name"], "params_hash": PH, "meta": {}}
          for c in dch]                                       # 06 §2.3 Chunk fields, in that order
print(f"spans: 07 {cfg} (07 params_hash {cfg.params_hash()}) -> {len(chunks)} chunks")
print(f"course params_hash over the 06 §2.4 chunking block = {PH} (expected 1ca9c5a3b548: {PH == '1ca9c5a3b548'})")
_jl = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")
print(f"chunks.jsonl bytes {len(_jl):,} sha256 {hashlib.sha256(_jl).hexdigest()} (C2 lab saved file: "
      f"d4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b; equal: "
      f"{hashlib.sha256(_jl).hexdigest() == 'd4108b8936093394c6eb50d4c22e8d4013d9a048fb38d5769281af4aadb3011b'})")
print("chunk 0:", {k: v for k, v in chunks[0].items() if k != "text"})
print("all per_page chunks have exactly one page segment:", all(len(c["page_segments"]) == 1 for c in chunks))
ids = [c["chunk_id"] for c in chunks]
print("chunk_id string order == seq order (zero-padded seq):", ids == sorted(ids))
lens = [len(c["text"]) for c in chunks]
print(f"chunk length chars min/median/max = {min(lens)}/{st.median(lens)}/{max(lens)}")

from sentence_transformers import SentenceTransformer  # noqa: E402
from huggingface_hub import snapshot_download  # noqa: E402

print("MiniLM snapshot:", os.path.basename(snapshot_download(MINILM, local_files_only=True)))
model = SentenceTransformer(MINILM, device="cpu")
V = model.encode([c["text"] for c in chunks], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
print(f"V shape={V.shape} dtype={V.dtype} max|norm-1|={np.abs(np.linalg.norm(V, axis=1) - 1).max():.2e} "
      f"bytes={V.nbytes:,}")

# write the three index files (06 §3.1) and read them back, as C4 will receive them from C3
tmp = Path(tempfile.mkdtemp(prefix="c4_index_"))   # stands in for index/<snapshot_id>/<params_hash>/<embed_hash>/
np.save(tmp / "vectors.npy", V)
with open(tmp / "chunks.jsonl", "w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
# embed_hash (course decision, 2026-10-08): 12 hex of sha256 over these six embedding fields; field VALUES as in C3's
# manifest (out_c3_measure.txt): input_type none/none, preproc_version none. Index folder:
# index/<snapshot_id>/<params_hash>/<embed_hash>/
EMB = {"provider": "sentence_transformers", "model_id": MINILM, "revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
       "input_type": {"documents": "none", "queries": "none"}, "normalize": True, "preproc_version": "none"}
EH = hashlib.sha256(json.dumps(EMB, sort_keys=True).encode("utf-8")).hexdigest()[:12]
print(f"embed_hash = {EH}; index folder index/{SNAP}/{PH}/{EH}/")
man = {"snapshot_id": SNAP, "chunking": CHUNKING, "params_hash": PH, "embedding": {**EMB, "dim": 384},
       "embed_hash": EH, "n_chunks": len(chunks)}
(tmp / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
V2 = np.load(tmp / "vectors.npy")
chunks2 = [json.loads(line) for line in open(tmp / "chunks.jsonl", encoding="utf-8")]
man2 = json.loads((tmp / "manifest.json").read_text(encoding="utf-8"))
assert len(V2) == len(chunks2) == man2["n_chunks"] and V2.dtype == np.float32
# row i of vectors.npy <-> line i of chunks.jsonl. seq restarts per document (Corpus T), so never assert seq == i.
assert len({c["chunk_id"] for c in chunks2}) == len(chunks2), "chunk_ids must be unique"
_last = {}
for c in chunks2:                                     # (doc_id, seq) strictly increasing within each doc_id
    assert c["seq"] > _last.get(c["doc_id"], -1); _last[c["doc_id"]] = c["seq"]
assert man2["embed_hash"] == EH
print(f"index round trip ({tmp.name}): vectors.npy {V2.shape} {V2.dtype}, chunks.jsonl {len(chunks2)} rows, "
      f"identical: {bool(np.array_equal(V, V2)) and chunks2 == json.loads(json.dumps(chunks))}")
V, chunks = V2, chunks2

# seeds (06 §6.7 machine-readable block), gold segments -> document offsets
seed_block = [b for b in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")][0]
SEEDS = [json.loads(line) for line in seed_block.splitlines() if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
TEXTS = {"climate": doc_text}
print(f"seeds: {len(SEEDS)} ({len(ANS)} answerable): {[s['qid'] for s in SEEDS]}")
Q = model.encode([s["question"] for s in SEEDS], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
QI = {s["qid"]: i for i, s in enumerate(SEEDS)}


def relv(i, s, chs):
    c = chs[i]
    return cc.rel(("climate", c["char_start"], c["char_end"]), s["G"], TEXTS)


def ce_at(order, s, chs, k):
    return cc.ce(s["G"], [("climate", chs[i]["char_start"], chs[i]["char_end"]) for i in order[:k]], TEXTS)


def gr_at(order, s, chs, k):
    return cc.group_recall(s["G"], [("climate", chs[i]["char_start"], chs[i]["char_end"]) for i in order[:k]], TEXTS)


def first_complete(order, s, chs):
    for r in range(1, len(order) + 1):
        if ce_at(order, s, chs, r):
            return r
    return None


# ---------------------------------------------------------------- S2
head("S2 the P5 setup reproduced (plain 1000/200 windows across pages, 91 chunks)")
wins = [(a, min(a + 1000, len(doc_text))) for a in range(0, len(doc_text), 800)]
import bisect  # noqa: E402

p5chunks = [{"chunk_id": f"{i:05d}", "doc_id": "climate", "char_start": a, "char_end": b, "text": doc_text[a:b],
             "page_segments": [{"page": bisect.bisect_right(starts, a)}]} for i, (a, b) in enumerate(wins)]
VP = model.encode([c["text"] for c in p5chunks], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
qd2 = Q[QI["D-002"]]
r5 = retrieve(qd2, VP, p5chunks, 6)
print(f"P5 setup: {len(p5chunks)} chunks; D-002 top-6:",
      [(int(r['chunk_id']), r['page'], round(r['score'], 4)) for r in r5])
print("P5 setup D-002 top-4 ids =", [int(r["chunk_id"]) for r in r5[:4]], "(P5 S3 found [64, 26, 16, 63])")
o5 = full_order(VP @ qd2, p5chunks)
print("P5 setup: rank of first relevant chunk for D-002 =",
      next(r for r, i in enumerate(o5, 1) if relv(i, SEEDS[QI["D-002"]], p5chunks)),
      "| first complete =", first_complete(o5, SEEDS[QI["D-002"]], p5chunks))

# ---------------------------------------------------------------- S3
head("S3 one query on the v0 index (D-002): shapes, top-8, the result records")
scores = V @ qd2
print(f"q shape {qd2.shape}, V shape {V.shape}, scores = V @ q shape {scores.shape}")
order = full_order(scores, chunks)
s2 = SEEDS[QI["D-002"]]
for r, i in enumerate(order[:8], 1):
    c = chunks[i]
    print(f"rank {r}: seq={c['seq']:3d} p.{c['page_segments'][0]['page']:2d} score={scores[i]:.4f} rel={relv(i, s2, chunks)} "
          f"'Paris Agreement' in text={'Paris Agreement' in c['text']} text={c['text'][:70]!r}")
res = retrieve(qd2, V, chunks, K)
print("top-4 seq:", [chunks[order[j]]["seq"] for j in range(4)], "fingerprint of seqs", fp([chunks[order[j]]["seq"] for j in range(4)]))
print("top-4 chunk_id fingerprint", fp([r["chunk_id"] for r in res]))
print("rank-1 result record (text cut):", json.dumps({**res[0], "text": res[0]["text"][:40] + "..."}))
print("result keys:", list(res[0].keys()))
print(f"D-002 score gaps rank1-2 {scores[order[0]]-scores[order[1]]:.5f}, rank2-3 {scores[order[1]]-scores[order[2]]:.5f}, "
      f"rank3-4 {scores[order[2]]-scores[order[3]]:.5f}, rank4-5 {scores[order[3]]-scores[order[4]]:.5f}")
print(f"score range over all {len(scores)} chunks: {scores.min():.4f} .. {scores.max():.4f}; median {np.median(scores):.4f}")
QB = Q @ V.T
print(f"all 10 seed questions at once: Q @ V.T shape {QB.shape} (queries x chunks)")

# ---------------------------------------------------------------- S4
head("S4 the 10 seeds on the v0 index: score tables, gaps, first evidence, distractors")
KEY = {"D-001": "1.2 degrees", "D-002": "Paris Agreement", "D-003": "NDC", "D-004": "DAC", "D-005": "carbon-intensive",
       "D-006": "solar", "D-007": "UNFCCC", "D-008": "Kigali", "D-009": "IPCC", "D-010": "emissions"}
rows = {}
for s in SEEDS:
    q = Q[QI[s["qid"]]]
    sc = V @ q
    o = full_order(sc, chunks)
    srt = sc[o]
    fr = next((r for r, i in enumerate(o, 1) if relv(i, s, chunks)), None) if s["answerable"] else None
    fc = first_complete(o, s, chunks) if s["answerable"] else None
    rel_all = [i for i in range(len(chunks)) if s["answerable"] and relv(i, s, chunks)]
    rows[s["qid"]] = {"order": o, "scores": sc, "first_rel": fr, "first_ce": fc, "n_rel": len(rel_all)}
    print(f"\n{s['qid']} ({s['category']}) {s['question']!r}")
    print(f"  top1={srt[0]:.4f} top2={srt[1]:.4f} top4={srt[3]:.4f} top5={srt[4]:.4f} gap1-2={srt[0]-srt[1]:.4f} "
          f"gap4-5={srt[3]-srt[4]:.4f} median={np.median(sc):.4f} within0.05oftop={int((sc >= srt[0]-0.05).sum())}")
    if s["answerable"]:
        print(f"  relevant chunks in index (any_overlap): {len(rel_all)} seqs={[chunks[i]['seq'] for i in rel_all]} "
              f"pages={[chunks[i]['page_segments'][0]['page'] for i in rel_all]}")
        print(f"  first relevant rank={fr} (score {srt[fr-1]:.4f}); first rank with CE=1: {fc}"
              + (f" (score {srt[fc-1]:.4f})" if fc else ""))
    for r, i in enumerate(o[:8], 1):
        c = chunks[i]
        print(f"    r{r} seq={c['seq']:3d} p.{c['page_segments'][0]['page']:2d} {sc[i]:.4f} "
              f"rel={relv(i, s, chunks) if s['answerable'] else '-'} key({KEY[s['qid']]})={KEY[s['qid']] in c['text']}")
    if s["answerable"] and fr and fr > 1:
        g = o[fr - 1]
        print(f"  outranking the first relevant chunk (seq {chunks[g]['seq']}, p.{chunks[g]['page_segments'][0]['page']}):")
        for r, i in enumerate(o[:fr - 1], 1):
            c = chunks[i]
            print(f"    r{r} seq={c['seq']} p.{c['page_segments'][0]['page']} score={sc[i]:.4f} "
                  f"margin over relevant={sc[i]-sc[g]:+.4f} cos(distractor, relevant chunk)={float(V[i] @ V[g]):.4f} "
                  f"key term present={KEY[s['qid']] in c['text']}")

print("\nsummary (v0 index, MiniLM): qid, first relevant rank, first CE rank, top1 score, gap1-2, gap4-5")
summ = []
for s in SEEDS:
    rr = rows[s["qid"]]
    srt = rr["scores"][rr["order"]]
    summ.append([s["qid"], rr["first_rel"], rr["first_ce"], round(float(srt[0]), 4), round(float(srt[0] - srt[1]), 4),
                 round(float(srt[3] - srt[4]), 4)])
    print("  ", summ[-1])
print("fingerprint of [qid, first_rel] for D-001..D-008:", fp([[s["qid"], rows[s["qid"]]["first_rel"]] for s in ANS]))
t1a = [float(rows[s["qid"]]["scores"][rows[s["qid"]]["order"][0]]) for s in ANS]
t1u = [float(rows[s["qid"]]["scores"][rows[s["qid"]]["order"][0]]) for s in SEEDS if not s["answerable"]]
print(f"top-1 score, answerable (8): min {min(t1a):.4f} median {st.median(t1a):.4f} max {max(t1a):.4f}; "
      f"unanswerable D-009, D-010: {[round(x, 4) for x in t1u]}")
print(f"answerable items whose top-1 score is below the HIGHER unanswerable top-1: "
      f"{sum(x < max(t1u) for x in t1a)}/8; below the LOWER one: {sum(x < min(t1u) for x in t1a)}/8")
gaps = []
for s in SEEDS:
    srt = rows[s["qid"]]["scores"][rows[s["qid"]]["order"]]
    gaps += [float(srt[j] - srt[j + 1]) for j in range(7)]
print(f"adjacent gaps inside the top-8 over 10 seeds (70 gaps): min {min(gaps):.5f} median {st.median(gaps):.5f} "
      f"max {max(gaps):.5f}; gaps < 0.01: {sum(g < 0.01 for g in gaps)}")

# ---------------------------------------------------------------- S5
head("S5 ties: real duplicates in the v0 index, chunk_id ordering")
by_text = {}
for i, c in enumerate(chunks):
    by_text.setdefault(c["text"], []).append(i)
dups = [v for v in by_text.values() if len(v) > 1]
print(f"exact duplicate chunk texts in the v0 index: {len(dups)} groups")
exact_ties = 0
for s in SEEDS:
    sc = rows[s["qid"]]["scores"]
    exact_ties += len(sc) - len(set(sc.tolist()))
print(f"exact score ties among all {len(chunks)} scores, summed over the 10 seeds: {exact_ties}")
# duplicate the index twice and shuffle the rows (lab CHECK 2d does the same)
rng = np.random.default_rng(7)
N = len(chunks)
Vd = np.vstack([V, V])
cd = chunks + [{**c, "chunk_id": f"climate:{SNAP}:{PH}:{c['seq'] + N:05d}", "seq": c["seq"] + N}
               for c in chunks]
perm = rng.permutation(2 * N)
Vd, cd = Vd[perm], [cd[i] for i in perm]
rd = retrieve(qd2, Vd, cd, K)
print("duplicated (x2) and shuffled index, D-002 top-4 seqs:", [int(r["chunk_id"][-5:]) for r in rd],
      "scores", [round(r["score"], 6) for r in rd])
sd = Vd @ qd2
naive = np.argsort(-sd, kind="stable")[:K]
print("  no tie rule (stable argsort of -score, i.e. row order): seqs", [cd[i]["seq"] for i in naive])
ap = np.argpartition(-sd, K - 1)[:K]
print("  argpartition only: seqs", [cd[i]["seq"] for i in ap])
toy = ["c:9", "c:10", "c:2"]
print("TOY: unpadded ids sorted as strings:", sorted(toy), "| padded:", sorted(["c:00009", "c:00010", "c:00002"]))

# ---------------------------------------------------------------- S6
head("S6 k sweep on the 8 answerable seeds (TOY ILLUSTRATION: 8 draft items, not an evaluation)")
import tiktoken  # noqa: E402

enc = tiktoken.get_encoding("o200k_harmony")
ctok = [len(enc.encode(c["text"])) for c in chunks]
print(f"tokenizer o200k_harmony (the Groq gpt-oss family, P1); chunk tokens min/median/max "
      f"{min(ctok)}/{st.median(ctok)}/{max(ctok)}")


def sweep(VV, chs, toks, label):
    out = {}
    for k in KS:
        hit = ce_ = gr = prec = 0
        tk_all = []
        for s in SEEDS:
            o = full_order(VV @ Q[QI[s["qid"]]], chs)
            tk_all.append(sum(toks[i] for i in o[:k]))
            if not s["answerable"]:
                continue
            rels = [relv(i, s, chs) for i in o[:k]]
            hit += int(any(rels))
            prec += sum(rels) / k
            ce_ += ce_at(o, s, chs, k)
            gr += gr_at(o, s, chs, k)
        n = len(ANS)
        miss = [s["qid"] for s in ANS if not ce_at(full_order(VV @ Q[QI[s["qid"]]], chs), s, chs, k)]
        out[k] = (hit, ce_, gr / n, prec / n, st.mean(tk_all))
        print(f"  {label} k={k}: Hit@k {hit}/{n}  CE@k {ce_}/{n}  Group-Recall@k {gr / n:.3f}  P@k {prec / n:.3f}  "
              f"mean context tokens (10 seeds) {st.mean(tk_all):.1f}  CE=0: {miss}")
    return out


sw = sweep(V, chunks, ctok, "v0")
print("  fingerprint [k, hit, ce] for k=1,2,4,8:", fp([[k, sw[k][0], sw[k][1]] for k in KS]))
print("  fingerprint of rounded mean tokens:", fp([round(sw[k][4]) for k in KS]))
for k in KS[1:]:
    print(f"  k {KS[KS.index(k)-1]} -> {k}: tokens x{sw[k][4] / sw[KS[KS.index(k)-1]][4]:.2f}")
print("  per-item first CE rank (v0):", {s["qid"]: rows[s["qid"]]["first_ce"] for s in ANS})
p5tok = [len(enc.encode(c["text"])) for c in p5chunks]
sweep(VP, p5chunks, p5tok, "P5-windows")

# ---------------------------------------------------------------- S7
head("S7 the query-embedding step (MC-002): same model, query side, scale")
raw_q = model.encode(SEEDS[QI["D-002"]]["question"], convert_to_numpy=True)
print(f"MiniLM encode(question) without normalize: norm {np.linalg.norm(raw_q):.6f} (the model ends with Normalize)")
qdoc = model.encode([SEEDS[QI["D-002"]]["question"]], normalize_embeddings=True, convert_to_numpy=True)[0]
print(f"MiniLM is symmetric: embedding the question 'as a document' (same encode call) -> max|diff| "
      f"{float(np.abs(qdoc - qd2).max()):.2e}")
print("OTHER model snapshot:", os.path.basename(snapshot_download(OTHER, local_files_only=True)))
m2 = SentenceTransformer(OTHER, device="cpu")
Q2 = m2.encode([s["question"] for s in SEEDS], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
print(f"wrong query model {OTHER}: query shape {Q2[0].shape} == index dim {V.shape[1]}: {Q2[0].shape[0] == V.shape[1]}; "
      f"V @ q raises no error: shape {(V @ Q2[0]).shape}")
hw = cw = 0
for s in ANS:
    o = full_order(V @ Q2[QI[s["qid"]]], chunks)
    hw += int(any(relv(i, s, chunks) for i in o[:K]))
    cw += ce_at(o, s, chunks, K)
print(f"  wrong query model, k=4: Hit@4 {hw}/8, CE@4 {cw}/8 (right model: Hit@4 {sw[4][0]}/8, CE@4 {sw[4][1]}/8)")
ow = full_order(V @ Q2[QI["D-002"]], chunks)
print("  D-002 top-4 with the wrong query model: seqs", [chunks[i]["seq"] for i in ow[:4]], "pages",
      [chunks[i]["page_segments"][0]["page"] for i in ow[:4]], "scores", [round(float((V @ Q2[QI['D-002']])[i]), 4) for i in ow[:4]])
print("  D-002 top-1 score: right model", round(float(scores[order[0]]), 4), "| wrong model",
      round(float((V @ Q2[QI['D-002']])[ow[0]]), 4))
q3 = qd2 * 3
r3 = retrieve(q3, V, chunks, K)
print(f"query scaled x3 (not normalised): same ids {[r['chunk_id'] for r in r3] == [r['chunk_id'] for r in res]}; "
      f"rank-1 score {r3[0]['score']:.4f} vs {res[0]['score']:.4f}")

# ---------------------------------------------------------------- S8
head("S8 broken retrieval variants on the 8 answerable seeds (k=4)")
ha = ca = 0
for s in ANS:
    o = np.argsort(V @ Q[QI[s["qid"]]])[:K].tolist()                     # ascending: forgot the minus
    ha += int(any(relv(i, s, chunks) for i in o))
    ca += ce_at(o, s, chunks, K)
asc = np.argsort(scores)[:K].tolist()
print(f"ascending sort: Hit@4 {ha}/8, CE@4 {ca}/8; D-002 'top-4' scores {[round(float(scores[i]), 4) for i in asc]}")
print("scores dropped (ids only, as retrieve_context_per_question does): the D-002 list would read",
      [chunks[i]["seq"] for i in order[:K]], "with no way to see the margin",
      f"{float(scores[order[0]] - scores[order[rows['D-002']['first_rel'] - 1]]):.4f} between rank 1 and the evidence")

# ---------------------------------------------------------------- S9
head("S9 lab fingerprints (CHECK cells)")
print("D-002 top-4 chunk_ids fp:", fp([r["chunk_id"] for r in res]))
print("D-002 top-4 scores rounded 4 fp:", fp([round(r["score"], 4) for r in res]))
print("first_rel per answerable seed fp:", fp({s["qid"]: rows[s["qid"]]["first_rel"] for s in ANS}))
print("first_ce per answerable seed fp:", fp({s["qid"]: rows[s["qid"]]["first_ce"] for s in ANS}))
print("sweep hit/ce fp:", fp({str(k): [sw[k][0], sw[k][1]] for k in KS}))
print("sweep mean tokens rounded fp:", fp({str(k): round(sw[k][4]) for k in KS}))
print("wrong-model hit/ce fp:", fp([hw, cw]))
print("dup+shuffle top-4 seqs fp:", fp([int(r["chunk_id"][-5:]) for r in rd]))
print("unanswerable top-1 scores rounded 2:", [round(x, 2) for x in t1u], "answerable min rounded 2:", round(min(t1a), 2))
