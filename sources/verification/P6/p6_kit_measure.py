"""P6 study-kit measurements (K1-K12): the real-corpus numbers the P6 HTML lesson adds on top of p6_measure.py (S1-S11).

Why a second script: p6_measure.py measured toys only. The study kit's running example is v0's **97 chunks** (the 07
recursive chunker, per page, 1000/200, as in P3's verify notebook, R1 and P4's K-run) with the 06 section 6.7 draft
seeds. p6_measure.py is not changed, so its saved output stays byte-identical.

Local only: no Groq, Cohere or Claude call, no .env read, no network. MiniLM loads from the local Hugging Face cache.
Labels: the draft seeds are LLM-drafted and not human-verified, so every number below is an observation on draft
seeds, never an evaluation result.

Run from rag_learning/:
    PYTHONIOENCODING=utf-8 uv run --group eval python sources/verification/P6/p6_kit_measure.py \
        "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf" > sources/verification/P6/out_p6_kit_measure.txt
Saved output: sources/verification/P6/out_p6_kit_measure.txt (sections K1..K12 for P6_FACTS.md section 1b)
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
import re
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pymupdf                                        # pinned 1.26.7
from rank_bm25 import BM25Okapi

PDF = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
L6 = "sentence-transformers/all-MiniLM-L6-v2"
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
sys.path.insert(0, str(HERE))
import p6_metrics as pm                               # noqa: E402
import p6_toy as toy                                  # noqa: E402

NORM_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")


def tok_norm(text):                                   # the course tokenizer (P3)
    return NORM_RE.findall(text.lower())


def head(t):
    print(f"\n=== {t}")


def f4(x):
    return f"{x:.4f}"


# ---------------------------------------------------------------- the 97 chunks and the draft seeds (as P3 verify / P4 K)
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
N = len(chunks)
PAGE = [c["page_segments"][0]["page"] for c in chunks]
RANGE = [("climate", c["char_start"], c["char_end"]) for c in chunks]
TEXTS = {"climate": "\n".join(pages)}
SEEDS = [json.loads(line) for line in cc.code_blocks(cc.section(md06, "6.7 Draft seed"), "jsonl")[0].splitlines()
         if line.strip()]
for s in SEEDS:
    s["G"] = [[[("climate", starts[seg["page"] - 1] + seg["char_start"], starts[seg["page"] - 1] + seg["char_end"])
                for seg in alt["segments"]] for alt in g["alternatives"]] for g in s["evidence_groups"]]
ANS = [s for s in SEEDS if s["answerable"]]
BYQ = {s["qid"]: s for s in SEEDS}
# binary qrels per seed: chunk seq -> 1 when the chunk overlaps any evidence (06 any_overlap); unlisted = 0
QRELS = {s["qid"]: {i: 1 for i in range(N) if cc.rel(RANGE[i], s["G"], TEXTS)} for s in ANS}
# which evidence group(s) each relevant chunk touches (G1, G2, ...)
TAGS = {s["qid"]: {i: [f"G{g + 1}" for g, grp in enumerate(s["G"]) if cc.rel(RANGE[i], [grp], TEXTS)]
                   for i in QRELS[s["qid"]]} for s in ANS}


def order(scores):
    """chunk seqs best first; ties broken by the smaller seq (the course rule)."""
    s = np.asarray(scores, float)
    return sorted(range(len(s)), key=lambda i: (-s[i], i))


def ce_k(ranking, s, k):
    return cc.ce(s["G"], [RANGE[i] for i in ranking[:k]], TEXTS)


def gr_k(ranking, s, k):
    return cc.group_recall(s["G"], [RANGE[i] for i in ranking[:k]], TEXTS)


def sc_k(ranking, s, k):
    return cc.span_coverage(s["G"], [RANGE[i] for i in ranking[:k]], TEXTS)


def row(ranking, s, k):
    q = QRELS[s["qid"]]
    return {"Hit": pm.hit_at_k(ranking, q, k), "P": pm.precision_at_k(ranking, q, k), "R": pm.recall_at_k(ranking, q, k),
            "RR": pm.reciprocal_rank(ranking, q, k), "nDCG": pm.ndcg_at_k(ranking, q, k), "CE": ce_k(ranking, s, k),
            "GR": gr_k(ranking, s, k), "SC": sc_k(ranking, s, k)}


def fmt_row(r):
    return (f"Hit {r['Hit']}  P {r['P']:.2f}  R {r['R']:.2f}  RR {r['RR']:.2f}  nDCG {r['nDCG']:.4f}  "
            f"CE {r['CE']}  Group-Recall {r['GR']:.2f}  Span-Coverage {r['SC']:.4f}")


def strip(ranking, s, n=5):
    out = []
    for i in ranking[:n]:
        t = TAGS[s["qid"]].get(i)
        out.append(f"s{i:03d} p.{PAGE[i]} " + ("YES(" + ",".join(t) + ")" if t else "no"))
    return " · ".join(out)


# ---------------------------------------------------------------- K1
head("K1 environment, corpus, labels")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in
      ("pymupdf", "rank-bm25", "sentence-transformers", "torch", "numpy", "ir-measures", "pytrec-eval-terrier")})
print("pdf sha256", hashlib.sha256(pdf_bytes).hexdigest())
print(f"chunks: count={N} params_hash={PH} snapshot={SNAP[:12]} chunks.jsonl sha256={SHA_JL}")
print(f"draft seeds: {len(SEEDS)} ({len(ANS)} answerable; unanswerable: {[s['qid'] for s in SEEDS if not s['answerable']]})")
for s in ANS:
    print(f"  {s['qid']} groups={len(s['G'])} relevant chunk seqs={sorted(QRELS[s['qid']])} "
          f"tags={ {f's{i:03d}': t for i, t in sorted(TAGS[s['qid']].items())} } pages={sorted({PAGE[i] for i in QRELS[s['qid']]})} "
          f"question={s['question']!r}")
nrel = [len(QRELS[s["qid"]]) for s in ANS]
print(f"n_rel per answerable seed: {nrel}; seeds with n_rel > 1: {sum(n > 1 for n in nrel)} of {len(ANS)}; "
      f"seeds with > 1 group: {sum(len(s['G']) > 1 for s in ANS)} of {len(ANS)}")

# ---------------------------------------------------------------- retrievers
BM = BM25Okapi([tok_norm(c["text"]) for c in chunks])
print(f"BM25 tok_norm on 97 chunks: avgdl={BM.avgdl:.2f} vocabulary={len(BM.idf)} (P3 verify: 111.23, 1769)")
BMS = {s["qid"]: BM.get_scores(tok_norm(s["question"])) for s in SEEDS}
DENSE = None
try:
    from sentence_transformers import SentenceTransformer  # noqa: E402
    m6 = SentenceTransformer(L6, device="cpu")
    E = m6.encode([c["text"] for c in chunks], normalize_embeddings=True, convert_to_numpy=True, batch_size=32,
                  show_progress_bar=False)
    DENSE = {s["qid"]: E @ m6.encode([s["question"]], normalize_embeddings=True, convert_to_numpy=True,
                                     show_progress_bar=False)[0] for s in SEEDS}
    print(f"MiniLM {L6}: dim={E.shape[1]}")
except Exception as e:                                # never fake: report and stop
    print("MiniLM could not load offline:", type(e).__name__, str(e)[:200])
    sys.exit(1)
RUN = {"dense": {q: order(v) for q, v in DENSE.items()}, "bm25": {q: order(v) for q, v in BMS.items()}}

# ---------------------------------------------------------------- K2
head("K2 the running example D-007, dense (MiniLM), k = 1..5 and 10")
s7 = BYQ["D-007"]
r7 = RUN["dense"]["D-007"]
print(f"question: {s7['question']!r}; groups={len(s7['G'])}; relevant={sorted(QRELS['D-007'])}")
print("dense top 5:", strip(r7, s7))
print("dense top-5 cosines:", [f4(DENSE["D-007"][i]) for i in r7[:5]])
for k in (1, 2, 3, 4, 5, 10):
    print(f"k={k:<2d} " + fmt_row(row(r7, s7, k)))
print("DCG/IDCG at k=2 and k=3 (binary, exp gain = linear gain):",
      [(k, f4(pm.dcg_at_k(r7, QRELS['D-007'], k)), f4(pm.idcg_at_k(QRELS['D-007'], k))) for k in (2, 3)])

# ---------------------------------------------------------------- K3
head("K3 D-007, BM25 (tok_norm)")
b7 = RUN["bm25"]["D-007"]
print("BM25 top 5:", strip(b7, s7))
print("BM25 top-5 scores:", [f4(BMS["D-007"][i]) for i in b7[:5]])
for k in (1, 2, 3, 4, 5, 10):
    print(f"k={k:<2d} " + fmt_row(row(b7, s7, k)))

# ---------------------------------------------------------------- K4
head("K4 D-005: counting chunks is not counting facts")
s5 = BYQ["D-005"]
print(f"question: {s5['question']!r}; groups={len(s5['G'])}; relevant={sorted(QRELS['D-005'])} tags={TAGS['D-005']}")
for name in ("dense", "bm25"):
    r = RUN[name]["D-005"]
    print(f"{name:5s} top 5: {strip(r, s5)}")
    for k in (1, 2, 4):
        print(f"      k={k} " + fmt_row(row(r, s5, k)))

# ---------------------------------------------------------------- K5
head("K5 the Precision@k ceiling n_rel / k on the seeds (k = 4)")
for s in ANS:
    n = len(QRELS[s["qid"]])
    print(f"  {s['qid']} n_rel={n} ceiling P@4 <= {min(n, 4) / 4:.2f} | dense P@4={pm.precision_at_k(RUN['dense'][s['qid']], QRELS[s['qid']], 4):.2f} "
          f"bm25 P@4={pm.precision_at_k(RUN['bm25'][s['qid']], QRELS[s['qid']], 4):.2f}")

# ---------------------------------------------------------------- K6
head("K6 every answerable seed, both retrievers (k = 4 for the set metrics; RR and nDCG at 10)")
MEAN = {}
for name in ("dense", "bm25"):
    print(f"-- {name}")
    rows = []
    for s in ANS:
        r = RUN[name][s["qid"]]
        q = QRELS[s["qid"]]
        first = next((j for j, i in enumerate(r, 1) if i in q), None)
        x = {"first": first, "Hit1": pm.hit_at_k(r, q, 1), "Hit4": pm.hit_at_k(r, q, 4), "P4": pm.precision_at_k(r, q, 4),
             "R4": pm.recall_at_k(r, q, 4), "RR10": pm.reciprocal_rank(r, q, 10), "nDCG10": pm.ndcg_at_k(r, q, 10),
             "CE4": ce_k(r, s, 4), "GR4": gr_k(r, s, 4)}
        rows.append(x)
        print(f"  {s['qid']} n_rel={len(q)} first relevant rank={first} Hit@1={x['Hit1']} Hit@4={x['Hit4']} P@4={x['P4']:.2f} "
              f"R@4={x['R4']:.2f} RR@10={x['RR10']:.4f} nDCG@10={x['nDCG10']:.4f} CE@4={x['CE4']} GroupRecall@4={x['GR4']:.2f}")
    m = {key: sum(x[key] for x in rows) / len(rows) for key in ("Hit1", "Hit4", "P4", "R4", "RR10", "nDCG10", "CE4", "GR4")}
    MEAN[name] = m
    print(f"  MEAN (n={len(rows)}): Hit@1={m['Hit1']:.3f} Hit@4={m['Hit4']:.3f} P@4={m['P4']:.4f} R@4={m['R4']:.4f} "
          f"MRR@10={m['RR10']:.4f} nDCG@10={m['nDCG10']:.4f} CE@4={m['CE4']:.3f} GroupRecall@4={m['GR4']:.4f}")
    print(f"  counts: Hit@1 {sum(x['Hit1'] for x in rows)}/8, Hit@4 {sum(x['Hit4'] for x in rows)}/8, "
          f"CE@4 {sum(x['CE4'] for x in rows)}/8")
print(f"MRR@10 rounded to 3: dense {MEAN['dense']['RR10']:.3f}, bm25 {MEAN['bm25']['RR10']:.3f} (P3 §12: 0.708, 0.938)")
for k in (1, 2, 3, 4):
    print(f"CE@{k} counts of 8: dense {sum(ce_k(RUN['dense'][s['qid']], s, k) for s in ANS)}, "
          f"bm25 {sum(ce_k(RUN['bm25'][s['qid']], s, k) for s in ANS)}")

# ---------------------------------------------------------------- K7
head("K7 why small sets are noisy: the values one RR@10 can take")
vals = sorted({Fraction(1, r) for r in range(1, 11)} | {Fraction(0)}, reverse=True)
print(f"possible RR@10 values ({len(vals)}):", [f"{float(v):.4f}" for v in vals])
for name in ("dense", "bm25"):
    rr = [pm.reciprocal_rank(RUN[name][s["qid"]], QRELS[s["qid"]], 10) for s in ANS]
    print(f"  {name}: RR@10 per seed {[round(v, 4) for v in rr]}; distinct values {sorted(set(round(v, 4) for v in rr))}")
d = [pm.reciprocal_rank(RUN['bm25'][s['qid']], QRELS[s['qid']], 10) - pm.reciprocal_rank(RUN['dense'][s['qid']], QRELS[s['qid']], 10)
     for s in ANS]
print(f"  per-seed difference bm25 - dense: {[round(v, 4) for v in d]}; seeds where they tie: {sum(abs(v) < 1e-12 for v in d)}")
print(f"  one seed moving from rank 2 to rank 1 changes MRR over 8 seeds by {0.5 / 8:.4f}")

# ---------------------------------------------------------------- K8
head("K8 R-precision and AP on toy Q1 (p6_toy; toy data)")
q1, r1 = toy.QRELS["Q1"], toy.RANKINGS["Q1"]
nrel1 = sum(g >= 1 for g in q1.values())
print(f"Q1 |Rel|={nrel1}; R-precision = P@{nrel1} = {pm.precision_at_k(r1, q1, nrel1):.4f}")
print(f"Q1 AP@10 standard={pm.average_precision(r1, q1, 10):.4f}; AP@5 standard={pm.average_precision(r1, q1, 5):.4f} "
      f"vs retrieved-relevant={pm.average_precision(r1, q1, 5, 'retrieved_relevant'):.4f}")
print(f"D-007 dense: AP@5 standard={pm.average_precision(r7, QRELS['D-007'], 5):.4f} "
      f"context precision@5={pm.average_precision(r7, QRELS['D-007'], 5, 'retrieved_relevant'):.4f}; "
      f"R-precision=P@{len(QRELS['D-007'])}={pm.precision_at_k(r7, QRELS['D-007'], len(QRELS['D-007'])):.4f}")
# the review item P6-A-06: relevant, not, not, relevant, not; 3 relevant exist
ra = ["r1", "n1", "n2", "r2", "n3"]
qa = {"r1": 1, "r2": 1, "r3": 1}
print(f"A-06 ranking R N N R N with 3 relevant: AP@5 standard={pm.average_precision(ra, qa, 5):.4f} "
      f"retrieved-relevant={pm.average_precision(ra, qa, 5, 'retrieved_relevant'):.4f}")

# ---------------------------------------------------------------- K9
head("K9 unjudged = not relevant, on the real corpus: labels from one retriever's pool")
print("Labels kept = only the relevant chunks that the POOL retriever put in its top D; everything else is unjudged = 0.")
print("Seeds whose pool holds no relevant chunk are dropped (n shown), so full and pool columns use the same seeds.")
for pool_name in ("bm25", "dense"):
    for D in (1, 2):
        for name in ("dense", "bm25"):
            full, part, holes, lost = {"MRR": [], "P4": [], "nDCG": []}, {"MRR": [], "P4": [], "nDCG": []}, 0, 0
            for s in ANS:
                q = QRELS[s["qid"]]
                pool = set(RUN[pool_name][s["qid"]][:D])
                qp = {i: 1 for i in q if i in pool}
                if not qp:
                    continue
                r = RUN[name][s["qid"]]
                for lab, store in ((q, full), (qp, part)):
                    store["MRR"].append(pm.reciprocal_rank(r, lab, 10))
                    store["P4"].append(pm.precision_at_k(r, lab, 4))
                    store["nDCG"].append(pm.ndcg_at_k(r, lab, 10))
                holes += sum(1 for i in r[:4] if i not in pool)
                lost += sum(1 for i in r[:4] if i in q and i not in qp)
            n = len(full["MRR"])
            mm = lambda v: sum(v) / len(v)  # noqa: E731
            print(f"  pool={pool_name} top {D} | scored: {name:5s} n={n} | MRR@10 {mm(full['MRR']):.4f} -> {mm(part['MRR']):.4f} | "
                  f"P@4 {mm(full['P4']):.4f} -> {mm(part['P4']):.4f} | nDCG@10 {mm(full['nDCG']):.4f} -> {mm(part['nDCG']):.4f} | "
                  f"unjudged top-4 slots {holes}/{4 * n} | truly relevant top-4 chunks scored 0: {lost}")

# ---------------------------------------------------------------- K10
head("K10 ties at the cut-off on the real runs (k = 4)")
for name, SC in (("dense", DENSE), ("bm25", BMS)):
    t = []
    for s in SEEDS:
        sc = np.asarray(SC[s["qid"]], float)
        r = order(sc)
        kth = sc[r[3]]
        n_at = int(np.sum(sc == kth))
        if n_at > 1:
            t.append((s["qid"], f4(kth), n_at))
    print(f"  {name}: seeds with a score tie at rank 4: {t if t else 'none'}")
zero = {s["qid"]: int(np.sum(BMS[s["qid"]] == 0)) for s in SEEDS}
print(f"  bm25 chunks scoring exactly 0 per seed: {zero}")

# ---------------------------------------------------------------- K11
head("K11 the same run, two tools: p6_metrics vs ir-measures (pytrec_eval backend)")
import ir_measures                                    # noqa: E402
from ir_measures import RR, Success, nDCG, P, R      # noqa: E402

# (a) the 8 seeds, both retrievers: binary labels, scores = rank-derived so that ties cannot occur
for name in ("dense", "bm25"):
    qrels = [ir_measures.Qrel(s["qid"], f"s{i:03d}", 1) for s in ANS for i in sorted(QRELS[s["qid"]])]
    run = [ir_measures.ScoredDoc(s["qid"], f"s{i:03d}", float(N - j)) for s in ANS for j, i in enumerate(RUN[name][s["qid"]])]
    agg = ir_measures.calc_aggregate([P @ 4, R @ 4, Success @ 4, RR @ 10, RR, nDCG @ 10], qrels, run)
    ours = {"P@4": MEAN[name]["P4"], "R@4": MEAN[name]["R4"], "Success@4": MEAN[name]["Hit4"], "RR@10": MEAN[name]["RR10"],
            "nDCG@10": MEAN[name]["nDCG10"]}
    print(f"  {name}: ir-measures " + ", ".join(f"{m}={v:.6f}" for m, v in sorted(agg.items(), key=lambda kv: str(kv[0]))))
    print(f"  {name}: p6_metrics  " + ", ".join(f"{m}={v:.6f}" for m, v in ours.items()))
    diff = max(abs(agg[m] - ours[str(m)]) for m in agg if str(m) in ours)
    print(f"  {name}: max |difference| over shared measures = {diff:.2e}")

# (b) graded toy: nDCG gain conventions (Q1 at k = 5; grades 2/1)
qrels = [ir_measures.Qrel("Q1", d, g) for d, g in toy.QRELS["Q1"].items()]
run = [ir_measures.ScoredDoc("Q1", d, float(10 - j)) for j, d in enumerate(toy.RANKINGS["Q1"])]
lin = ir_measures.calc_aggregate([nDCG @ 5], qrels, run)[nDCG @ 5]
qx = [ir_measures.Qrel("Q1", d, 2 ** g - 1) for d, g in toy.QRELS["Q1"].items()]   # map grades to 2^g - 1 ourselves
ex = ir_measures.calc_aggregate([nDCG @ 5], qx, run)[nDCG @ 5]
print(f"  toy Q1 nDCG@5: ir-measures default (gain = qrels value) {lin:.4f}; same with grades mapped to 2^g - 1 {ex:.4f}; "
      f"p6_metrics exp {pm.ndcg_at_k(toy.RANKINGS['Q1'], toy.QRELS['Q1'], 5):.4f}, linear "
      f"{pm.ndcg_at_k(toy.RANKINGS['Q1'], toy.QRELS['Q1'], 5, 'linear'):.4f}")

# (c) ties: two docs with the same score; trec_eval ignores the run order and breaks ties by docno
qt = [ir_measures.Qrel("T", "a", 1)]
rt = [ir_measures.ScoredDoc("T", "a", 1.0), ir_measures.ScoredDoc("T", "b", 1.0), ir_measures.ScoredDoc("T", "c", 0.5)]
ours_t = pm.reciprocal_rank(["a", "b", "c"], {"a": 1}, 10)       # course rule: ties by (-score, id) -> a first
print(f"  tie demo (a and b both score 1.0; a relevant): course rule RR={ours_t:.4f}; "
      f"ir-measures RR={ir_measures.calc_aggregate([RR], qt, rt)[RR]:.4f}; P@1={ir_measures.calc_aggregate([P @ 1], qt, rt)[P @ 1]:.4f}")

# (d) cut-off: RR with no cut-off vs RR@10, for a first hit at rank 12
qc = [ir_measures.Qrel("C", "h", 1)]
rc = [ir_measures.ScoredDoc("C", f"x{j:02d}", float(100 - j)) for j in range(11)] + [ir_measures.ScoredDoc("C", "h", 50.0)]
a = ir_measures.calc_aggregate([RR, RR @ 10], qc, rc)
print(f"  cut-off demo (first relevant at rank 12): RR (no cut-off, trec_eval recip_rank) = {a[RR]:.4f}; RR@10 = {a[RR @ 10]:.4f}; "
      f"p6_metrics RR@10 = {pm.reciprocal_rank([f'x{j:02d}' for j in range(11)] + ['h'], {'h': 1}, 10):.4f}")

# ---------------------------------------------------------------- K12
head("K12 MRR and nDCG on the seeds: where the two retrievers differ")
for s in ANS:
    q = QRELS[s["qid"]]
    dd, bb = RUN["dense"][s["qid"]], RUN["bm25"][s["qid"]]
    print(f"  {s['qid']}: RR@10 dense {pm.reciprocal_rank(dd, q, 10):.4f} bm25 {pm.reciprocal_rank(bb, q, 10):.4f} | "
          f"nDCG@10 dense {pm.ndcg_at_k(dd, q, 10):.4f} bm25 {pm.ndcg_at_k(bb, q, 10):.4f} | "
          f"relevant ranks in top 10: dense {[j for j, i in enumerate(dd[:10], 1) if i in q]} "
          f"bm25 {[j for j, i in enumerate(bb[:10], 1) if i in q]}")
print("\ndone")
