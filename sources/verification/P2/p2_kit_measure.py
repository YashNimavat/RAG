"""P2 study-kit measurements (K1-K6): the numbers the HTML lesson adds on top of p2_measure.py (S1-S11).

Local only: no Groq, Cohere or Claude call, no .env read. MiniLM loads from the local Hugging Face cache (offline).
p2_measure.py is not changed, so its saved output stays byte-identical. Same toy corpus, tokenizer, overlap
ranking (ties by doc id ascending) and MiniLM ranking as p2_measure.py S2-S8.

Run from rag_learning/:
    uv run python sources/verification/P2/p2_kit_measure.py "<Book RAG>/upstream/RAG_Techniques/data/Understanding_Climate_Change.pdf"
Saved output: sources/verification/P2/out_p2_kit_measure.txt  (sections K1..K6 for P2_FACTS.md section 1b)
"""
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import importlib.metadata as md
import json
import re
import sys
from collections import Counter

import numpy as np
import pymupdf as fitz                                # pinned 1.26.7

PDF = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
toy = json.load(open(os.path.join(HERE, "p2_toy_corpus.json"), encoding="utf-8"))
DOCS, QUERIES = toy["docs"], toy["queries"]
GRADE = {(r["qid"], r["did"]): r["grade"] for r in toy["qrels"]}
dids, qids = sorted(DOCS), sorted(QUERIES)
REL = {q: sorted(d for d in dids if GRADE.get((q, d), 0) >= 1) for q in qids}


def head(t):
    print(f"\n=== {t}")


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


toks = {d: tokenize(t) for d, t in DOCS.items()}
index = {}
for d in dids:
    for term in sorted(set(toks[d])):
        index.setdefault(term, []).append(d)


def overlap_scores(query):
    acc = Counter()
    for t in set(tokenize(query)):
        for d in index.get(t, []):
            acc[d] += 1
    return acc


def rank_lex(query, desc_ties=False):
    acc = overlap_scores(query)
    if desc_ties:                                          # ties broken by doc id DESCENDING
        return [d for d, _ in sorted(acc.items(), key=lambda x: (-x[1], [-ord(c) for c in x[0]]))]
    return [d for d, _ in sorted(acc.items(), key=lambda x: (-x[1], x[0]))]


def precision(ret, rel):
    return 0.0 if not ret else len(set(ret) & set(rel)) / len(ret)


def recall(ret, rel):
    return float("nan") if not rel else len(set(ret) & set(rel)) / len(rel)


def first_rank(ret, rel):
    return next((i for i, d in enumerate(ret, 1) if d in rel), None)


# ---------------------------------------------------------------- K1
head("K1 environment")
print("python", sys.version.split()[0], "|", {p: md.version(p) for p in ("pymupdf", "numpy", "sentence-transformers", "scikit-learn")})

# ---------------------------------------------------------------- K2 ties
head("K2 the tie rule decides the rank (q4, overlap ranking; relevant = d09)")
for name, desc in (("doc id ascending (S5 rule)", False), ("doc id descending", True)):
    run = rank_lex(QUERIES["q4"], desc)
    fr = first_rank(run, REL["q4"])
    print(f"{name:28s} run={run} scores={[overlap_scores(QUERIES['q4'])[d] for d in run]} first relevant rank={fr} RR={1/fr:.2f}")

# ---------------------------------------------------------------- MiniLM ranking (as S6)
from sentence_transformers import SentenceTransformer  # noqa: E402

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
D = model.encode([DOCS[d] for d in dids], normalize_embeddings=True)
Q = model.encode([QUERIES[q] for q in qids], normalize_embeddings=True)
S = Q @ D.T
DENSE = {q: [dids[j] for j in sorted(range(len(dids)), key=lambda j: (-S[i, j], dids[j]))] for i, q in enumerate(qids)}
LEX = {q: rank_lex(QUERIES[q]) for q in qids}

# ---------------------------------------------------------------- K3 recall@k curves
head("K3 set recall at k = 1..10 (lexical returns only its candidates; dense ranks all 10 docs)")
for name, runs in (("lexical", LEX), ("MiniLM", DENSE)):
    q1 = [round(recall(runs["q1"][:k], REL["q1"]), 3) for k in range(1, 11)]
    mean = [round(float(np.mean([recall(runs[q][:k], REL[q]) for q in qids])), 3) for k in range(1, 11)]
    print(f"{name:8s} q1   recall@1..10 = {q1}")
    print(f"{name:8s} mean recall@1..10 = {mean}")
print("lexical candidates per query:", {q: len(LEX[q]) for q in qids})

# ---------------------------------------------------------------- K4 pool demo
head("K4 labels built only from the lexical top 3 (a one-retriever pool), scored at k = 4")
K, POOL_K = 4, 3
pool = {q: set(LEX[q][:POOL_K]) for q in qids}
REL_POOL = {q: sorted(d for d in REL[q] if d in pool[q]) for q in qids}
print("pool (judged docs) per query:", {q: sorted(pool[q]) for q in qids})
print("relevant under pooled labels:", REL_POOL, "| under full labels:", REL)
for name, runs in (("lexical", LEX), ("MiniLM", DENSE)):
    rows = []
    for q in qids:
        top = runs[q][:K]
        judged = sum(1 for d in top if d in pool[q])
        rows.append((q, top, judged, precision(top, REL[q]), precision(top, REL_POOL[q]), recall(top, REL[q]), recall(top, REL_POOL[q])))
        print(f"{name:8s} {q} top{K}={top} judged@{K}={judged}/{len(top) if top else 0} "
              f"P@{K} full={precision(top, REL[q]):.3f} pooled={precision(top, REL_POOL[q]):.3f} "
              f"recall full={recall(top, REL[q]):.3f} pooled={recall(top, REL_POOL[q]):.3f}")
    jud = [r[2] / K for r in rows]
    print(f"{name:8s} mean Judged@{K} (out of {K} slots)={np.mean(jud):.3f}  mean P@{K} full={np.mean([r[3] for r in rows]):.3f} "
          f"pooled={np.mean([r[4] for r in rows]):.3f}  mean recall full={np.nanmean([r[5] for r in rows]):.3f} "
          f"pooled={np.nanmean([r[6] for r in rows]):.3f} (pooled recall averaged over {sum(1 for r in rows if not np.isnan(r[6]))} queries with a pooled relevant doc)")

# ---------------------------------------------------------------- K5 span labels -> chunk labels on 91 windows
head("K5 06 section 6.7 draft seeds: evidence spans -> relevant windows (any_overlap, non-whitespace), 91 windows of 1,000 / step 800")
pages = [p.get_text() for p in fitz.open(PDF)]
full = "\n".join(pages)
starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]
wins = [(i, min(i + 1000, len(full))) for i in range(0, len(full), 800)]
plan = open(os.path.join(WS, "06_RAG_PROJECT_AND_EVALUATION_PLAN.md"), encoding="utf-8").read()
block = plan.split("Machine-readable form (offsets: PyMuPDF 1.26.7")[1].split("```jsonl")[1].split("```")[0]
seeds = [json.loads(line) for line in block.strip().splitlines()]


def hits(a, b):
    return [w for w, (x, y) in enumerate(wins) if any(not ch.isspace() for ch in full[max(x, a):min(y, b)])]


print(f"windows={len(wins)} seeds={len(seeds)}")
for s in seeds:
    per_alt, allw = [], set()
    for g in s["evidence_groups"]:
        for alt in g["alternatives"]:
            ws = set()
            for seg in alt["segments"]:
                a = starts[seg["page"] - 1] + seg["char_start"]
                b = starts[seg["page"] - 1] + seg["char_end"]
                assert full[a:b].split()[:3] == alt["quote"].split()[:3], (s["qid"], full[a:b][:40])
                ws |= set(hits(a, b))
            per_alt.append(f"{g['group_id']}/{alt['alt_id']} p.{alt['segments'][0]['page']}->{sorted(ws)}")
            allw |= ws
    print(f"{s['qid']} ({s['category']}): relevant windows={sorted(allw)}  {'; '.join(per_alt)}")

# ---------------------------------------------------------------- K6 kappa, IIR Table 8.2
head("K6 agreement between two judges: IIR Table 8.2 counts (yes-yes 300, yes-no 20, no-yes 10, no-no 70)")
yy, yn, ny, nn = 300, 20, 10, 70
n = yy + yn + ny + nn
pa = (yy + nn) / n
p_rel = ((yy + yn) + (yy + ny)) / (2 * n)
pe = p_rel ** 2 + (1 - p_rel) ** 2
print(f"P(A)={pa:.4f} P(relevant, pooled marginals)={p_rel:.4f} P(E)={pe:.4f} kappa={(pa - pe) / (1 - pe):.4f}")
from sklearn.metrics import cohen_kappa_score  # noqa: E402

j1 = [1] * yy + [1] * yn + [0] * ny + [0] * nn
j2 = [1] * yy + [0] * yn + [1] * ny + [0] * nn
print(f"Cohen's kappa (separate marginals, scikit-learn) = {cohen_kappa_score(j1, j2):.4f}")
print("DONE")
